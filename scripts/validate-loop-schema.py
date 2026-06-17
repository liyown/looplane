#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "loop-result.schema.json"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "loop-results"


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def get_prop(schema, *path):
    node = schema
    for key in path:
        node = node["properties"][key]
    return node


def assert_schema_shape(schema):
    props = schema["properties"]
    require("requestedWorker" in props, "schema must define requestedWorker")
    require(
        props["requestedWorker"]["enum"] == [
            "discovery",
            "memory-reconcile",
            "repo-manager",
            "coordinator",
            None,
        ],
        "requestedWorker enum must stay small and actor-oriented",
    )
    require("ctoAction" not in props, "schema must not expose centralized ctoAction")
    require("escalation" in props, "schema must define escalation")
    require(
        set(props["escalation"]["properties"].keys())
        >= {"target", "kind", "blocking", "reason"},
        "escalation must include target, kind, blocking, and reason",
    )

    discovery_target = get_prop(schema, "discoveryReport", "target")
    require(
        set(discovery_target.get("required", []))
        >= {"kind", "status", "repo", "confidence", "evidence"},
        "discoveryReport.target must require target identity fields",
    )
    require(
        discovery_target.get("additionalProperties") is False,
        "discoveryReport.target must reject unknown target fields",
    )

    brief = props["executionBrief"]
    require(
        set(brief.get("required", []))
        >= {
            "goal",
            "nonGoals",
            "acceptanceCriteria",
            "target",
            "verification",
            "risks",
        },
        "executionBrief must require the Todo brief core fields",
    )


def validate_target(target):
    required = {"kind", "status", "repo", "confidence", "evidence"}
    missing = required - set(target)
    require(not missing, f"target missing required fields: {sorted(missing)}")
    require(target["kind"] in {"unknown", "no-code", "parent", "code"}, "bad target.kind")
    require(target["status"] in {"unresolved", "inferred", "confirmed"}, "bad target.status")
    require(target["confidence"] in {"low", "medium", "high"}, "bad target.confidence")
    require(isinstance(target["evidence"], list), "target.evidence must be an array")


def validate_result(result):
    require(result["status"] in {"completed", "blocked", "no_op", "failed"}, "bad status")
    require(result.get("reason"), "reason is required")
    observed = result["observed"]
    for field in ("issueId", "runId", "loop", "fingerprint"):
        require(observed.get(field), f"observed.{field} is required")

    if "requestedWorker" in result:
        require(
            result["requestedWorker"]
            in {"discovery", "memory-reconcile", "repo-manager", "coordinator", None},
            "bad requestedWorker",
        )

    require("ctoAction" not in result, "result must not use centralized ctoAction")

    if result.get("escalation") is not None:
        escalation = result["escalation"]
        for field in ("target", "kind", "blocking", "reason"):
            require(field in escalation, f"escalation.{field} is required")

    if result.get("discoveryReport") is not None:
        report = result["discoveryReport"]
        for field in (
            "issueId",
            "target",
            "repoHead",
            "baseBranch",
            "inspectedPaths",
            "likelyChangeAreas",
            "verificationCandidates",
            "unknowns",
            "createdAt",
            "freshness",
        ):
            require(field in report, f"discoveryReport.{field} is required")
        validate_target(report["target"])

    if result.get("executionBrief") is not None:
        brief = result["executionBrief"]
        for field in (
            "goal",
            "nonGoals",
            "acceptanceCriteria",
            "target",
            "discoveryReportRef",
            "likelyChangeAreas",
            "verification",
            "risks",
            "rollback",
        ):
            require(field in brief, f"executionBrief.{field} is required")
        validate_target(brief["target"])


def main():
    schema = load_json(SCHEMA_PATH)
    assert_schema_shape(schema)

    failures = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = load_json(path)
        expect_valid = fixture["expectValid"]
        try:
            validate_result(fixture["result"])
            valid = True
            error = None
        except AssertionError as exc:
            valid = False
            error = str(exc)

        if valid != expect_valid:
            failures.append(f"{path.name}: expected valid={expect_valid}, got valid={valid}: {error}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print(f"validated schema shape and {len(list(FIXTURE_DIR.glob('*.json')))} fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
