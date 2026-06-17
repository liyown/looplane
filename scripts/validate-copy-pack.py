#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_PROMPT_DIR = ROOT / "dist" / "zh-CN" / "prompts"

EXPECTED_PROMPTS = {
    "initial-loop.standalone.md",
    "triage-loop.standalone.md",
    "backlog-loop.standalone.md",
    "discovery-loop.standalone.md",
    "todo-loop.standalone.md",
    "in-progress-loop.standalone.md",
    "in-review-loop.standalone.md",
    "done-loop.standalone.md",
    "canceled-loop.standalone.md",
    "duplicate-loop.standalone.md",
    "memory-reconcile-loop.standalone.md",
    "repo-manager.standalone.md",
    "coordinator-loop.standalone.md",
}

FORBIDDEN_FRAGMENTS = [
    "prompts/_shared-contract.md",
    "../schemas",
    "schemas/loop-result.schema.json",
    "Return JSON per `prompts/_shared-contract.md`",
    "Output Contract",
    "runner_gap",
    "runner must",
    "The local runner should",
    "~/.linear-loop/memory/",
    "memory/discovery",
    "memory/runs",
]

SPOT_CHECKS = [
    "initial-loop.standalone.md",
    "triage-loop.standalone.md",
    "todo-loop.standalone.md",
    "repo-manager.standalone.md",
]

REQUIRED_SNIPPETS = [
    "~/.linear-loop",
    "~/.linear-loop/state/",
    "~/.linear-loop/runtime-issues/",
    "Loop Final Report",
    "Linear issue",
    "Project docs",
    "Return only a JSON object",
    "runtimeIssues",
    "compare-and-set",
    "re-read Linear",
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_prompt(path):
    text = path.read_text(encoding="utf-8")
    for fragment in FORBIDDEN_FRAGMENTS:
        require(fragment not in text, f"{path.name} leaks source reference: {fragment}")


def main():
    require(DIST_PROMPT_DIR.exists(), "dist/zh-CN/prompts is missing")
    generated = {path.name for path in DIST_PROMPT_DIR.glob("*.standalone.md")}
    require(generated == EXPECTED_PROMPTS, f"unexpected standalone prompt set: {sorted(generated)}")

    for path in sorted(DIST_PROMPT_DIR.glob("*.standalone.md")):
        validate_prompt(path)

    for name in SPOT_CHECKS:
        text = (DIST_PROMPT_DIR / name).read_text(encoding="utf-8")
        for snippet in REQUIRED_SNIPPETS:
            require(snippet in text, f"{name} missing required snippet: {snippet}")

    print(f"validated copy pack shape and {len(generated)} standalone prompts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
