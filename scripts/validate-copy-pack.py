#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_PROMPT_DIR = ROOT / "dist" / "zh-CN" / "prompts"

EXPECTED_PROMPTS = {
    "initial-setup.standalone.md",
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
    "Loop Final Report",
    "Return only a JSON object",
    "Return JSON per the shared",
    "Return JSON matching",
    "final report shape",
    "requestedWorker",
    "runtimeIssues[]",
    "runtimeIssues",
    "schema_gap",
    "run" + "ner_gap",
    "run" + "ner must",
    "The local " + "run" + "ner should",
    "~/.linear-loop/memory/",
    "memory/discovery",
    "memory/runs",
    "initial-loop",
    "Initial loop",
    "Initial Loop",
    "Paste this whole file",
    "Use this as the prompt body",
    "## Run Mode",
    "## Role Prompt",
    "Standalone Prompt",
]

SPOT_CHECKS = [
    "initial-setup.standalone.md",
    "triage-loop.standalone.md",
    "todo-loop.standalone.md",
    "repo-manager.standalone.md",
]

REQUIRED_SNIPPETS = [
    "~/.linear-loop",
    "~/.linear-loop/state/",
    "~/.linear-loop/runtime-issues/",
    "Markdown `Run Note`",
    "Do not return JSON as a run contract",
    "Linear issue",
    "Project docs",
    "runtime issue records",
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
