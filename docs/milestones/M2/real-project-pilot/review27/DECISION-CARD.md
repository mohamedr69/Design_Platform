# Budget decision card (owner)

**Decide: approve or decline** a new model budget for the four-arm experiment, running exactly declaration **`6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1`**. Declaration v1 (`aec4d4df…`) is superseded, and an approval of it does not carry over.

| Item | What you would approve |
|---|---|
| Request caps | **at most 688 application-visible requests**: A 8 · L1 160 · L2 160 · L3 180 · L4 180, in new ledger scopes `m2-four-arm-final-2026-10-01-{A,L1,L2,L3,L4}`. One CLI request may contain several provider-internal turns |
| Tokens | thresholds of 4 M input / 600 k output per scope and 70 k / 20 k per request, applied to **estimates before dispatch**; actual usage is recorded afterwards, and an overshoot opens a breaker that stops **further** requests. **The `claude-code` CLI cannot enforce actual token limits; there is no hard actual-token bound** |
| Cost | **unknown**; no authoritative price exists for the declared provider |
| Elapsed lifetime (proposed) | 96 h per document-arm scope, 4 h for A, from first use; **not a completion guarantee** |
| Existing limits kept | 12 requests per document (durable); 60 per project per rolling 24 h across tracks; whole-project deferral with zero requests |
| Labels | `r26.2`: AI-drafted, then an independent owner-delegated **AI** source review (Review 27); not human, not blind; the Word control D27 is not visually verified |
| ROI sample limitation | only 3 decision-bearing drawing sheets are crop-eligible (D16–D18, one project, 2 explicit stamps); the A4-form decisions (D04, D19, D22) are read whole-page. This is a small diagnostic, not proof of decision safety |
| Stops | terminal: critical acceptance on a resolved label, or 3 consecutive provider failures (never resumed). Budget stops: caps, token breaker, elapsed, allowance, rolling counter. Refusals before dispatch for any binding change |
| What it cannot do | establish general accuracy, choose a default or accept M2 |

Nothing is scheduled or dispatched while this decision is pending.
