# Knowledge Compilation — Architecture Design Document

> This document defines the complete design of the **Knowledge Compilation** methodology: compile an expert's tacit experience into deterministic, executable rules so that weak open-source small models can perform expert tasks at near-zero cost. Unlike training distillation (which changes weights), Knowledge Compilation is inference-time injection (which provides instructions).

---

## 1. Core Insights

### 1.1 Inference Offloading
An expert's tacit knowledge → compiled into decision criteria, success/failure standards, and step-by-step if-then rules → **the agent only executes, never thinks**.
This is not "teaching" an agent; it's "reasoning for" the agent.

### 1.2 A Consumption Philosophy Designed for Weak Models
Mainstream knowledge frameworks target **flagship models**: knowledge is a "reference" and the model still thinks for itself.
Knowledge Compilation is the **reverse design**: the knowledge framework's target consumer is a "dumb" model, so the structure must be foolproof —
**decision trees set direction, hard rules block errors, verified checklists remove reasoning, and the meta-skill enforces "just follow, don't think."**

### 1.3 Cost Arbitrage
Because the knowledge pack is "dumb" enough and deterministic, weaker open-source models (10-100x cheaper) can do the same job.
**The more complete the knowledge → the less reasoning required → the cheaper the model you can use.**

### 1.4 Compilation × Distillation = the Biggest Cost-Reduction Lever for Domain Tasks
Distillation (training phase, done by model vendors) solves the small model's "can't think" foundation; Compilation (inference phase, this methodology) solves "doesn't know" — domain experience.
Together: **small-model foundation (can think) + expert domain judgment (knows) = small-model cost, with strong-model reasoning plus expert domain expertise.**
Boundary: applies to knowledge-dense, reasoning-thin tasks; open-ended reasoning tasks still need strong models.

---

## 2. Why "Compilation", Not "Distillation"

| | Knowledge Distillation | **Knowledge Compilation** |
|---|---|---|
| Phase | Training time | Inference time |
| Method | Train/fine-tune small model weights with large model outputs | Compile experience into deterministic rule frameworks injected into context |
| Cost | Training cost (GPU, data, time) | Zero training cost — docs + injection only |
| Auditability | Black box (weights not inspectable) | White box (every rule, hard-rule and checklist is auditable) |
| Portability | Retrain per model | Same knowledge pack reused across models and harnesses |
| Applicability | General capability transfer | Domain experience transfer + task cost reduction |

Distillation changes the model's "muscle memory"; compilation gives the model an "operating manual".

---

## 3. Three-Layer Meta-Skill System (Distill → Package → Compile)

```
knowledge-distillation   → Produce knowledge (thinker: analyze, verify, summarize, document pitfalls)
knowledge-packaging      → Package knowledge (organizer: structure into portable packs)
knowledge-compilation ★  → Consume knowledge (executor: just follow, don't think)
```

### First Rule of Consuming Knowledge: Follow, Don't Think

| Behavior | Result |
|---|---|
| Follow (dumb) | ✅ Reproduces verified success |
| Improvise (clever) | ❌ Breaks verified flows, hits new pitfalls |

**Cognitive inversion**: a knowledge pack that a "dumb" agent can follow without error is the highest-quality deliverable. Be smart when *producing* knowledge (during distillation), not when *consuming* it (during execution).

### Four Consumption Guidelines

1. **Don't re-reason**: if the pack says "connect it this way," connect it that way. Don't "I think it should be..."
2. **Don't doubt verified conclusions**: measured values beat intuition / official docs
3. **Don't improvise**: don't "optimize" verified flows
4. **Check the pack first, then ask the user**: follow the pack if it has the answer; only ask if it doesn't

### Production vs Consumption Division

| Phase | Role | Behavior |
|---|---|---|
| Distill / produce knowledge | Thinker | Analyze, verify, summarize, document pitfalls |
| Compile / consume knowledge | Executor | Follow, don't doubt, only change adjustable items |

**Don't be a thinker during execution** — this is the biggest misconception in Knowledge Compilation.

---

## 4. Knowledge Pack Structure (Compiled Knowledge Pack, Five Layers)

```
SKILL.md        → decision tree (direction) + hard rules (constraints) + verified checklist
pipelines.md    → verified end-to-end pipelines
components.md   → reusable components (loops, templates, tools)
nodes.md        → measured values (parameter semantics, cross-system pitfalls, pitfalls log)
executable code → real scripts paired with the docs (tool layer)
```

### Hard Rules Example (from the runninghub-nodes knowledge pack)

1. LoRA/CLIP/VAE are bound to their base model; cross-system usage is forbidden
2. Nodes don't exist independently — assemble per pipelines; only build verified combinations, never invent new connections
3. Sampling parameters are bound to their system (applying across systems = unverified)
4. On errors, check measured values first (model names / LoRA cross-system / widget order)
5. Prompt systems don't mix: edit uses TextEncodeQwenImageEditPlus, text-to-image uses CLIPTextEncode
6. Grid tuning uses loop components, don't copy-paste modules
7. Base model ≠ task-specific: reuse base models across tasks, but components must follow the base model

Hard rules are the core of "compilation output": **write down the expert's judgment boundaries; a weak model can't reason, so you reason for it.**

---

## 5. Relationship with the Harness

Knowledge Compilation is injected at **inference time** through an agent harness:
- The harness provides the agent loop, tool protocol, and context management (infrastructure)
- The knowledge pack provides domain judgment (content)
- Statistical evaluation validates the pack's effectiveness (guardrail)

Layering principle:
- **Production** of knowledge packs (distillation): thinker role, done in real practice by humans/AI
- **Consumption** of knowledge packs (compilation): executor role, the agent follows
- **Validation** of knowledge packs: statistical methods (knowledge density vs reasoning density → whether to compile; controlled experiments → compilation effectiveness)

---

## 6. Validation & Evolution

### Decision Guidelines (When to Follow vs When to Innovate)

| Situation | Behavior |
|---|---|
| Pack has a clear answer | Follow (100% execution) |
| Pack marks "adjustable" | May change (within safe range) |
| Pack marks "hard rule / don't reverse / don't delete" | Absolutely do not change |
| Pack doesn't cover it | Ask the user (don't guess, don't invent) |
| New pitfall found after success | Write it back into the pack (this is distillation — the innovation phase) |

### Positive Loop

The knowledge-pack system moves toward **"more patterns → less reasoning required"** — a positive loop that never reaches zero: "unexpected cases" not covered by the docs still require model reasoning. This is the boundary of Knowledge Compilation.

---

## 7. Implementation Path

1. **Distill**: extract knowledge from real practice (successful cases → decision rules → hard rules)
2. **Package**: structure into portable knowledge packs (five-layer structure)
3. **Compile**: inject into open-source small models for consumption (just follow, don't think)
4. **Validate**: controlled experiments quantifying cost reduction (cost difference vs quality difference)
5. **Replicate**: a second, third domain knowledge pack — proving the methodology is reproducible
