"""One floor of a drawing's review, asked of the model on a fixed call budget
in this process only (app.review.scoped) -- the validation run.

    rehearsal (no model is called; on a copy of the database):
    venv\\Scripts\\python scripts\\scoped_drawing_review.py --database-url sqlite:///C:/copy.db ^
        --ep 30880 --drawing 1 --page 3 --floor "GROUND FLOOR" --sha 66043c11fab9eaf5a1768ba2 ^
        --max-calls 4 --max-turns 2 --report rehearsal.json

    the live run (the platform's AI route, AI_PROVIDER; only once it is approved):
    venv\\Scripts\\python scripts\\scoped_drawing_review.py --live --approved ^
        --ep 30880 --drawing 1 --page 3 --floor "GROUND FLOOR" --sha 66043c11fab9eaf5a1768ba2 ^
        --max-calls 4 --max-turns 2 --report validation.json

`.env` is not changed: the API and the workers keep the review's AI off
throughout. Exit 0 when the job finished, 1 when it did not, 2 when the
run was refused before anything was asked.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ep", required=True, help="the project's EP number")
    parser.add_argument("--drawing", type=int, required=True, help="the IFC drawing's id")
    parser.add_argument("--page", type=int, required=True, help="the sheet's page index on the plot")
    parser.add_argument("--floor", required=True, help="the floor that page must be")
    parser.add_argument("--sha", required=True, help="the drawing file's SHA-256 (12 characters at least)")
    parser.add_argument("--max-calls", type=int, required=True)
    parser.add_argument("--max-turns", type=int, required=True)
    parser.add_argument("--inline-images", action="store_true",
                        help="the pictures inside the message: no Read turn a picture (one turn a call is then enough)")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--database-url", help="another database (a copy for the rehearsal)")
    parser.add_argument("--live", action="store_true", help="the model, through AI_PROVIDER (costs usage)")
    parser.add_argument("--approved", action="store_true", help="the live run was approved")
    parser.add_argument("--skip-rooms", type=int, default=0, help="rehearsal: leave this many rooms a call unanswered")
    parser.add_argument("--fail", action="store_true", help="rehearsal: every call fails")
    args = parser.parse_args(argv)
    if args.live and not args.approved:
        print("The live run calls the model: pass --approved once it has been approved.", file=sys.stderr)
        return 2
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from app.ai import provider as prov  # noqa: E402
    from app.core.config import get_settings  # noqa: E402
    from app.review import scoped  # noqa: E402

    scope = scoped.Scope(ep_number=args.ep, drawing_id=args.drawing, page=args.page, floor=args.floor,
                         source_sha=args.sha, max_calls=args.max_calls, max_turns=args.max_turns,
                         inline_images=args.inline_images)
    if args.live:
        factory = lambda: prov._build(get_settings())  # noqa: E731 -- built inside the run's settings
    else:
        turns = 1 if args.inline_images else 2                  # pictures inline: one turn a call
        factory = lambda: scoped.RehearsalProvider(skip_rooms=args.skip_rooms, fail=args.fail, turns=turns)  # noqa: E731
    try:
        report = scoped.run(scope, factory, report_path=args.report)
    except scoped.Refused as exc:
        print(f"Refused: {exc}", file=sys.stderr)
        return 2
    job = report.get("job") or {}
    review = report.get("review") or {}
    print(json.dumps({"job": job.get("status"), "error": job.get("error"), "stopped": report.get("stopped"),
                      "invocations": len(report.get("invocations") or []),
                      "turns": [i.get("turns") for i in report.get("invocations") or []],
                      "state": review.get("state"), "floor": review.get("floor"),
                      "findings": len(review.get("findings") or []),
                      "settings_after": report.get("settings_after"),
                      "env_file_unchanged": report.get("env_file_unchanged")}, indent=2, default=str))
    return 0 if job.get("status") == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
