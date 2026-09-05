"""
Knowledge Compilation Harness — Minimal Runnable Demo
=====================================================

The core thesis: "Follow, Don't Think."

A weak model cannot reliably reason about safety. So the harness doesn't ask it
to reason — it compiles the knowledge pack's hard rules into deterministic code
guardrails and enforces them with if-else, not with LLM judgment.

Pipeline shown here:
    SKILL.md (human-readable hard rules)
        → [compilation step] → compiled knowledge pack (machine-readable JSON)
        → harness loads the pack → intercepts rule violations at runtime
        → white-box audit log (every decision is inspectable)

Run: python demo_harness.py
"""

import json
import sys
from dataclasses import dataclass, field

# Windows consoles default to GBK; force UTF-8 so the emoji output renders.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ============================================================
# 1. The Compiled Knowledge Pack
#    (in real engineering, produced by the compilation step from SKILL.md;
#     here it is inline for the demo)
# ============================================================
COMPILED_KNOWLEDGE_PACK = {
    "skill_name": "RunningHub Workflow Operation",
    "version": "1.0",
    "compiled_from": "runninghub-nodes/SKILL.md §3 hard rules",
    "hard_rules": [
        {
            "id": "R01",
            "when": {"action": "run_workflow"},
            # LoRA/CLIP/VAE are bound to their base model family:
            # output["lora_family"] must equal output["model_family"]
            "field_match": {"lora_family": "model_family"},
            "error": "LoRA/CLIP/VAE are bound to their base model; cross-system mixing is forbidden",
        },
        {
            "id": "R02",
            "when": {"action": "delete"},
            "forbidden_values": {"target": ["workflows/", "production_db"]},
            "error": "Deleting protected resources is forbidden",
        },
        {
            "id": "R03",
            "when": {"action": "deploy"},
            "required_fields": ["rollback_plan"],
            "error": "Deploy requires a rollback plan",
        },
    ],
}


# ============================================================
# 2. The Weak Model (simulated)
# ============================================================

# Case A: the weak model hallucinates — it "thinks" running a Qwen-edit
# workflow with a Z-Image LoRA is fine (cross-system mixing).
weak_model_output_A = {
    "action": "run_workflow",
    "workflow": "char_workflow",
    "model_family": "qwen_edit",
    "lora_family": "z_image",  # violates R01
    "reasoning": "The LoRA loads fine, let's just run it.",
}

# Case B: the weak model tries to delete the workflows directory
# (the classic over-reach / hallucination of authority).
weak_model_output_B = {
    "action": "delete",
    "target": "workflows/",
    "reasoning": "User asked to clean up space, I deleted it.",
}


# ============================================================
# 3. Knowledge Compilation Harness — the "iron supervisor"
# ============================================================
class KCHarness:
    def __init__(self, knowledge_pack: dict):
        self.knowledge_pack = knowledge_pack
        self.audit_log: list[dict] = []  # white-box audit trail

    # --- public API -------------------------------------------------
    def execute(self, model_output: dict) -> dict:
        violations = self._check(model_output)
        if violations:
            return self._block(model_output, violations)
        self.audit_log.append(
            {"status": "SUCCESS", "action": model_output.get("action"), "output": model_output}
        )
        print(f"  ✅ [harness] all rules passed, executing action: {model_output['action']}")
        return {"status": "SUCCESS", "action": model_output["action"]}

    # --- rule engine (deterministic if-else, no LLM judgment) -------
    def _check(self, output: dict) -> list[dict]:
        violations = []
        for rule in self.knowledge_pack["hard_rules"]:
            if not self._matches(rule["when"], output):
                continue  # rule not applicable to this action
            if "field_match" in rule:
                a, b = list(rule["field_match"].items())[0]
                if output.get(a) != output.get(b):
                    violations.append(rule)
            if "forbidden_values" in rule:
                for field, banned in rule["forbidden_values"].items():
                    if output.get(field) in banned:
                        violations.append(rule)
            if "required_fields" in rule:
                for f in rule["required_fields"]:
                    if f not in output:
                        violations.append(rule)
        return violations

    def _matches(self, when: dict, output: dict) -> bool:
        return all(output.get(k) == v for k, v in when.items())

    # --- interception + forced retry -------------------------------
    def _block(self, output: dict, violations: list[dict]) -> dict:
        for rule in violations:
            self.audit_log.append(
                {
                    "status": "BLOCKED",
                    "rule_id": rule["id"],
                    "error": rule["error"],
                    "output": output,
                }
            )
            print(f"  🛑 [harness] hard rule [{rule['id']}] triggered: {rule['error']}")
            # inject the violated rule back into context, forcing regeneration
            print(f"  🔄 [harness] injecting rule [{rule['id']}] into context, "
                  f"forcing the weak model to regenerate...")
        return {
            "status": "REJECTED",
            "violated_rules": [r["id"] for r in violations],
            "retry_required": True,
            "injected_rules": violations,  # what was fed back to the model
        }

    # --- audit ------------------------------------------------------
    def dump_audit_log(self) -> str:
        return json.dumps(self.audit_log, ensure_ascii=False, indent=2)


# ============================================================
# 4. Demo: an agent loop where the harness supervises
# ============================================================
def run_demo_case(harness: KCHarness, label: str, bad_output: dict, fixed_output: dict):
    print("=" * 66)
    print(f"🧪 {label}")
    print(f"  🤖 weak model output: {bad_output}")

    # First attempt — the weak model violates a hard rule
    result = harness.execute(bad_output)
    if result["status"] == "REJECTED":
        # The harness blocked it and forced regeneration.
        # Here we simulate the corrected output after rule injection.
        print(f"  🤖 weak model (after rule injection): {fixed_output}")
        result = harness.execute(fixed_output)

    print()


def main():
    print("Knowledge Compilation Harness — minimal demo")
    print("Thesis: Follow, Don't Think. Rules are compiled to code, not left to model judgment.\n")

    harness = KCHarness(COMPILED_KNOWLEDGE_PACK)

    run_demo_case(
        harness,
        "Test 1: weak model tries cross-system LoRA (R01)",
        bad_output=weak_model_output_A,
        fixed_output={
            "action": "run_workflow",
            "workflow": "char_workflow",
            "model_family": "qwen_edit",
            "lora_family": "qwen_edit",  # corrected: same family
            "reasoning": "Following the pack: LoRA must match the base model.",
        },
    )

    run_demo_case(
        harness,
        "Test 2: weak model tries to delete protected resources (R02)",
        bad_output=weak_model_output_B,
        fixed_output={
            "action": "delete",
            "target": "tmp_outputs/",  # corrected: safe target
            "reasoning": "Following the pack: protected paths are off-limits.",
        },
    )

    print("=" * 66)
    print("📋 White-box audit log (every decision is inspectable):")
    print(harness.dump_audit_log())


if __name__ == "__main__":
    main()
