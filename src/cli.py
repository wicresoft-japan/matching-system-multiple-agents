"""
Bidirectional matching CLI.
Usage: python -m src.cli --profiles data/profiles.json --projects data/projects.json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import asdict
from pathlib import Path

from src.models import load_profiles, load_projects
from src.matcher import bidirectional_match


def _pct(score: float) -> str:
    """Format a 0.0-1.0 score as a whole-number percentage string, e.g. '67%'."""
    return f"{round(score * 100)}%"


def _skills_str(skills: list[str]) -> str:
    """Join skill names with ', '."""
    return ", ".join(skills)


def _print_table(results: dict) -> None:
    """Print bidirectional match results in a human-readable table format."""
    profile_matches = results.get("profile_matches", {})
    project_matches = results.get("project_matches", {})

    # --- Profile -> Project ---
    print("=== 経歴 → 案件マッチング ===\n")
    if not profile_matches:
        print("（マッチングデータがありません）\n")
    else:
        for source_key, matches in profile_matches.items():
            if matches:
                name = matches[0].source_name
            else:
                name = source_key
            print(f"{name} ({source_key}):")
            if not matches:
                print("  （該当案件なし）")
            else:
                for i, m in enumerate(matches, 1):
                    skills = _skills_str(m.matched_skills)
                    print(
                        f"  {i}. {m.target_name} ({m.target_id})"
                        f" - スコア: {_pct(m.score)}"
                        f" (マッチスキル: {skills})"
                    )
            print()

    # --- Project -> Profile ---
    print("=== 案件 → 経歴マッチング ===\n")
    if not project_matches:
        print("（マッチングデータがありません）\n")
    else:
        for source_key, matches in project_matches.items():
            if matches:
                name = matches[0].source_name
            else:
                name = source_key
            print(f"{name} ({source_key}):")
            if not matches:
                print("  （該当経歴なし）")
            else:
                for i, m in enumerate(matches, 1):
                    skills = _skills_str(m.matched_skills)
                    print(
                        f"  {i}. {m.target_name} ({m.target_id})"
                        f" - スコア: {_pct(m.score)}"
                        f" (マッチスキル: {skills})"
                    )
            print()


def _results_to_dict(results: dict) -> dict:
    """Recursively convert MatchResult dataclass instances to plain dicts."""
    converted: dict = {}
    for direction, mapping in results.items():
        converted[direction] = {}
        for key, match_list in mapping.items():
            converted[direction][key] = [asdict(m) for m in match_list]
    return converted


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Bidirectional matching CLI — match profiles to projects and vice versa.",
    )
    parser.add_argument(
        "--profiles",
        required=True,
        type=Path,
        help="Path to the profiles JSON file.",
    )
    parser.add_argument(
        "--projects",
        required=True,
        type=Path,
        help="Path to the projects JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to output JSON file. If omitted, results are printed to stdout.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help='Output format: "table" (human-readable) or "json" (raw JSON). Default: table.',
    )

    args = parser.parse_args(argv)

    # --- Load profiles ---
    profiles_path: Path = args.profiles
    if not profiles_path.exists():
        print(f"Error: profiles file not found: {profiles_path}", file=sys.stderr)
        sys.exit(1)
    try:
        profiles = load_profiles(str(profiles_path))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in profiles file: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Load projects ---
    projects_path: Path = args.projects
    if not projects_path.exists():
        print(f"Error: projects file not found: {projects_path}", file=sys.stderr)
        sys.exit(1)
    try:
        projects = load_projects(str(projects_path))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in projects file: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Run matching ---
    results = bidirectional_match(profiles, projects)

    # --- Output ---
    if args.format == "json":
        output_json = json.dumps(
            _results_to_dict(results), ensure_ascii=False, indent=2
        )
        if args.output:
            args.output.write_text(output_json, encoding="utf-8")
            print(f"Results written to {args.output}")
        else:
            print(output_json)
    else:
        if args.output:
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                _print_table(results)
            finally:
                sys.stdout = old_stdout
            output_text = buf.getvalue()
            args.output.write_text(output_text, encoding="utf-8")
            print(f"Results written to {args.output}")
        else:
            _print_table(results)


if __name__ == "__main__":
    main()
