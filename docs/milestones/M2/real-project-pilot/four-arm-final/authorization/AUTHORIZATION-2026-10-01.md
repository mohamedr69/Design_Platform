# Owner authorization (recorded verbatim, 2026-10-01T15:36:51Z UTC)

I explicitly approve the execution of declaration `6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1`.

Approved ledger scopes and application-visible request caps:

- `m2-four-arm-final-2026-10-01-A`: 8 requests
- `m2-four-arm-final-2026-10-01-L1`: 160 requests
- `m2-four-arm-final-2026-10-01-L2`: 160 requests
- `m2-four-arm-final-2026-10-01-L3`: 180 requests
- `m2-four-arm-final-2026-10-01-L4`: 180 requests
- Maximum total: 688 application-visible requests

Approved token thresholds:

- Per request: 70,000 estimated input tokens and 20,000 estimated output tokens
- Per scope: 4,000,000 estimated input tokens and 600,000 estimated output tokens

I understand that these are pre-dispatch estimates, not hard limits on actual Claude Code CLI token usage. A request can exceed a threshold before the circuit breaker prevents later requests. The monetary cost is unknown.

Approved elapsed limits:

- A: 4 hours
- L1–L4: 96 hours per scope

This authorization applies only to the frozen declaration, projects, labels, provider, models, harness, order, stop conditions and limits bound by the declaration hash above.

Do not change the sample, models, scopes, limits, labels, stop rules or declaration. Do not reopen terminally stopped arms. Do not use sealed projects. Record this message verbatim as the owner authorization, run the read-only preflight, and stop without sending a model request if any binding or safety check fails.

After preflight passes, you are authorized to start the declared experiment and manually resume deferred arms under the same declaration until they complete, stop terminally or reach their approved limits. Report every dispatch, deferral, stop and remaining allowance. This authorization does not approve a default variant, production use, M2 acceptance or M3.
