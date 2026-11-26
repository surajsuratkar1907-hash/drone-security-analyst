"""Command-line interface.

    python -m drone_agent run                       # process frames, build the index
    python -m drone_agent query --object truck      # search the index
    python -m drone_agent ask "what objects were in the video?"
    python -m drone_agent summary
    python -m drone_agent ui                        # web dashboard at http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import os
import sys

from .agent import SecurityAnalystAgent
from .indexer import FrameIndex
from .models import load_frames, parse_time
from .qa import answer, summarize_day

DEFAULT_FRAMES = os.path.join("data", "frames.json")
DEFAULT_DB = os.path.join("data", "index.db")


def _require_db(path: str) -> None:
    if not os.path.exists(path):
        print(f"No index found at {path}. Run: python -m drone_agent run", file=sys.stderr)
        raise SystemExit(1)


def cmd_run(args: argparse.Namespace) -> int:
    frames = load_frames(args.frames)
    if os.path.exists(args.db):
        os.remove(args.db)  # always rebuild from scratch
    index = FrameIndex(args.db)
    results = SecurityAnalystAgent(index=index).run(frames)

    for result in results:
        for line in result.logs:
            print(f"LOG    frame {result.frame_id:>3} | {line}")
        for alert in result.alerts:
            print(f"ALERT  frame {result.frame_id:>3} | [{alert.severity.upper()}] {alert.message}")

    print()
    print(summarize_day(index))
    print(f"Index written to {args.db}")
    index.close()
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    _require_db(args.db)
    index = FrameIndex(args.db)
    start = parse_time(args.start) if args.start else None
    end = parse_time(args.end) if args.end else None

    if args.logs:
        rows = index.list_logs(label=args.object, color=args.color)
        for r in rows:
            print(f"{r['time']}  {r['text']}")
    elif args.object or args.color:
        rows = index.frames_with_object(args.object, args.color, args.location, start, end)
        for r in rows:
            detail = " ".join(p for p in (r["label"], r["color"], r["action"]) if p)
            print(f"frame {r['frame_id']:>3} | {r['time']} | {r['location']:<11} | {detail}")
        if args.object:
            entries = index.count_entries(args.object, args.color, args.location, args.action)
            print(f"Entries ('{args.action}' episodes): {entries}")
    else:
        rows = index.frames_in_range(start, end, args.location)
        for r in rows:
            print(f"frame {r['frame_id']:>3} | {r['time']} | {r['location']:<11} | {r['description']}")

    print(f"{len(rows)} matching row(s).")
    index.close()
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    _require_db(args.db)
    index = FrameIndex(args.db)
    print(answer(index, " ".join(args.question)))
    index.close()
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    _require_db(args.db)
    index = FrameIndex(args.db)
    print(summarize_day(index))
    index.close()
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    from .dashboard import serve

    if not os.path.exists(args.db):
        print("No index yet, building it first...")
        cmd_run(argparse.Namespace(frames=args.frames, db=args.db))
        print()
    serve(args.db, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="drone_agent", description="Drone Security Analyst Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="process frames and build the index")
    p_run.add_argument("--frames", default=DEFAULT_FRAMES)
    p_run.add_argument("--db", default=DEFAULT_DB)
    p_run.set_defaults(func=cmd_run)

    p_query = sub.add_parser("query", help="search indexed frames, logs and entries")
    p_query.add_argument("--db", default=DEFAULT_DB)
    p_query.add_argument("--object", help="label, e.g. truck, person, van, car, animal")
    p_query.add_argument("--color", help="e.g. blue, white, grey")
    p_query.add_argument("--location", help="e.g. 'Main Gate'")
    p_query.add_argument("--start", help="HH:MM")
    p_query.add_argument("--end", help="HH:MM")
    p_query.add_argument("--action", default="entering", help="action used for entry counting")
    p_query.add_argument("--logs", action="store_true", help="show log events instead of frames")
    p_query.set_defaults(func=cmd_query)

    p_ask = sub.add_parser("ask", help="ask a follow-up question")
    p_ask.add_argument("--db", default=DEFAULT_DB)
    p_ask.add_argument("question", nargs="+")
    p_ask.set_defaults(func=cmd_ask)

    p_sum = sub.add_parser("summary", help="one-sentence summary of the day")
    p_sum.add_argument("--db", default=DEFAULT_DB)
    p_sum.set_defaults(func=cmd_summary)

    p_ui = sub.add_parser("ui", help="open the web dashboard in your browser")
    p_ui.add_argument("--frames", default=DEFAULT_FRAMES)
    p_ui.add_argument("--db", default=DEFAULT_DB)
    p_ui.add_argument("--port", type=int, default=8000)
    p_ui.set_defaults(func=cmd_ui)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
