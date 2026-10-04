# Approved-Only Drawn Set (owner decision 1; F002, F003 exposure, F035)

## Rule

`_drawn(c)` (`service.py:713`) is the one predicate that decides what Apply makes. The page's "will be drawn" flag, the `counts.drawn` total and the Apply button's count are all computed from the same function in `view()`:

```
drawn(c) = c.status == "approved"
           and (c.remove or c.insert)
           and (not requires_confirmation(c) or c.confirmed is True)

requires_confirmation(c) = c.insert and c.action == "add" and not c.moved
                           and c.residual is not None and c.residual > CONFIRM_ABOVE_M (1.0 m)
```

- The comparison is exact (`"approved"`): `proposed`, `skipped`, `failed`, `pending`, rejected, held, uncertain, `None` and any other spelling are all excluded.
- The rule is the same for add, remove and replace, and for review changes and interface modules. The old exception (review changes drawn while `proposed`) is gone.
- Acceptance in the Drawings Review is not approval for drawing. The engineer must approve the placed change on the Redesign page.
- Confirmation: `PATCH …/changes/{id}` accepts `confirmed: true` (`routers/redesign.py:121,131`), and `adjust()` stores it. Any re-placement through `adjust()` (point, candidate, symbol, rotation) clears it again, so a confirmed spot never silently becomes a different spot.
- The Apply POST refuses with 422 when nothing is drawn (`routers/redesign.py:106-108`). `apply()` refuses again when the drawn set is empty.

## The page

- The count card says "Proposed, not drawn until approved"; the old wording was "Placed, to approve".
- Every proposed change shows "not drawn until approved", and an approved, drawn one shows "will be drawn".
- A change still to be confirmed shows a "Confirm this spot" button.
- The Apply button reads "Make redesigned drawing (N approved)", where N is `counts.drawn`.

## GC-01 effect (from the RD-M1 snapshot)

| | Old rule | RD-M2 rule |
|---|---|---|
| Drawn changes | 11 | 11 |
| …of which review changes still `proposed` | 0 | 0 (excluded by rule) |
| Changes needing confirmation | 0 (max residual 0.55 m) | 0 |
| RD-M1 F003 change `d89599d510abfedf` (skipped, low-confidence REMOVE) | not drawn (skipped) | not drawn; it would also be excluded if it were `proposed` |

The current GC-01 drawn set is unchanged because the engineer had already approved or skipped every review change. The fix closes the path by which an unapproved AI placement or erase could be drawn.

## Tests

`test_only_explicitly_approved_changes_are_drawn`, `test_proposed_and_skipped_changes_stay_out_of_the_apply`, `test_a_skipped_low_confidence_remove_like_rd_m1_f003_is_never_drawn`, `test_a_spot_to_confirm_is_drawn_only_once_confirmed`, `test_the_page_says_a_proposed_change_is_not_drawn_and_asks_for_approval_before_an_apply`, `test_nothing_approved_means_no_apply_job`, plus the updated `test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved`.

## Not addressed (out of scope)

F003's cause, which is AI answers being accepted regardless of confidence or notes, is unchanged. RD-M2 only closes its route to the drawing.
