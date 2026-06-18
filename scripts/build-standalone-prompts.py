#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "prompts"
DIST_PROMPT_DIR = ROOT / "dist" / "zh-CN" / "prompts"
SHARED_CONTRACT = PROMPT_DIR / "_shared-contract.md"

PROMPT_FILES = [
    "initial-setup.md",
    "triage-loop.md",
    "backlog-loop.md",
    "discovery-loop.md",
    "todo-loop.md",
    "in-progress-loop.md",
    "in-review-loop.md",
    "done-loop.md",
    "canceled-loop.md",
    "duplicate-loop.md",
    "memory-reconcile-loop.md",
    "repo-manager.md",
    "coordinator-loop.md",
]


def title_for(path):
    return path.stem.replace("-", " ").title()


def sanitize_source(text):
    replacements = {
        "`prompts/_shared-contract.md`": "the embedded Shared Loop Contract above",
        "prompts/_shared-contract.md": "the embedded Shared Loop Contract above",
        "`schemas/loop-result.schema.json`": "the embedded Loop Final Report",
        "schemas/loop-result.schema.json": "the embedded Loop Final Report",
        "../schemas": "the embedded Loop Final Report",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.rstrip()


def render_prompt(path, shared_contract):
    source = sanitize_source(path.read_text(encoding="utf-8"))
    title = title_for(path)
    if path.name == "initial-setup.md":
        usage = """Run this whole file manually once in your local agent. Do not put it on a
recurring schedule."""
        runtime_note = "- This initial setup prompt runs once and does not own a recurring Linear state.\n"
    else:
        usage = "Paste this whole file into the matching local AG schedule or worker."
        runtime_note = ""
    return f"""# {title} Standalone Prompt

{usage}

This prompt is self-contained. It embeds the shared loop contract, final report shape,
and local Loop Space rules. Do not ask the user to open files from this repository
while the prompt is running.

## Runtime Assumptions

{runtime_note}- The prompt or worker runs locally and can access `~/.linear-loop`.
- Linear remains the visible state and collaboration surface.
- `~/.linear-loop` stores minimal runtime state, locks, cooldowns, repo cache,
  worktrees, lesson candidates, and runtime issue logs.
- Repository origins and default verification commands come only from Linear Project
  `Agent Project Settings`.
- A loop performs its own allowed Linear, GitHub, filesystem, and local state changes.
- A state loop may write Linear only after it re-reads Linear and local state and the
  observed snapshot still matches.
- Discovery reports and Todo briefs belong on the Linear issue.
- Long-lived experience memory belongs in Linear Project docs.

## Embedded Shared Loop Contract

{shared_contract.rstrip()}

## Role Prompt

{source}
"""


def expected_outputs():
    shared = sanitize_source(SHARED_CONTRACT.read_text(encoding="utf-8"))
    outputs = {}
    for name in PROMPT_FILES:
        source_path = PROMPT_DIR / name
        output_path = DIST_PROMPT_DIR / f"{source_path.stem}.standalone.md"
        outputs[output_path] = render_prompt(source_path, shared)
    return outputs


def write_outputs(outputs):
    DIST_PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    for stale_path in DIST_PROMPT_DIR.glob("*.standalone.md"):
        if stale_path not in outputs:
            stale_path.unlink()
    for output_path, text in outputs.items():
        output_path.write_text(text, encoding="utf-8")


def check_outputs(outputs):
    failures = []
    for output_path, expected in outputs.items():
        if not output_path.exists():
            failures.append(f"{output_path.relative_to(ROOT)} is missing")
            continue
        actual = output_path.read_text(encoding="utf-8")
        if actual != expected:
            failures.append(f"{output_path.relative_to(ROOT)} is stale")
    stale = sorted(
        path
        for path in DIST_PROMPT_DIR.glob("*.standalone.md")
        if path not in outputs
    )
    for path in stale:
        failures.append(f"{path.relative_to(ROOT)} is not generated from a source prompt")
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated standalone prompts are up to date",
    )
    args = parser.parse_args()

    outputs = expected_outputs()
    if args.check:
        failures = check_outputs(outputs)
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print(f"standalone prompts are up to date ({len(outputs)} files)")
        return 0

    write_outputs(outputs)
    print(f"generated {len(outputs)} standalone prompts in {DIST_PROMPT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
