# Knowledge Compilation

> **Compile expert tacit experience into deterministic, executable rules, so that weak open-source models can perform expert tasks at near-zero cost — no training, no distillation, fully auditable.**

---

## One-Line Positioning

In the era of AI generation, **generation is commoditizing fast; judgment is not.** This project proposes **Knowledge Compilation** — a knowledge-engineering methodology designed for *weak-model consumption*: compile an expert's tacit reasoning (decision criteria, success/failure standards, if-then flows) into a deterministic framework of decision trees + hard rules + verified checklists, then inject it at **inference time** through an agent harness into an open-source small model.

The model doesn't need to get smarter — **the framework thinks for it.**

---

## Why "Compilation", Not "Distillation"?

| | Knowledge Distillation | **Knowledge Compilation** |
|---|---|---|
| Phase | Training time | Inference time |
| Method | Train/fine-tune small model weights with large model outputs | Compile experience into deterministic rule frameworks injected into context |
| Cost | Training cost (GPU, data, time) | Zero training cost — docs + injection only |
| Auditability | Black box (weights not inspectable) | White box (every rule, hard-rule and checklist is auditable) |
| Portability | Retrain per model | Same knowledge pack reused across models and harnesses |
| Applicability | General capability transfer | **Domain experience transfer + task cost reduction** |

Distillation changes the model's "muscle memory"; compilation gives the model an "operating manual". Distillation is *teaching it to learn*; compilation is *thinking for it*.

---

## Why It's the Biggest Cost-Reduction Lever: Compilation × Distillation

**Knowledge Compilation + Knowledge Distillation = the strongest combination for cutting costs in domain tasks.**

| | Distillation (training) | Compilation (inference) |
|---|---|---|
| Solves | **"Can't think"** — small model's baseline capability | **"Doesn't know"** — small model's domain experience |
| Done by | Model vendors (DeepSeek, Phi, etc.) | Application layer (this repo) |
| Cost | One-time training cost, amortized | Zero training cost, reused continuously |
| Output | Small models with general capability | Deterministic frameworks that can do expert work |

- **Distillation alone**: the small model has baseline capability but no domain knowledge — still can't do an expert's job
- **Compilation alone**: the model is too weak even at baseline — knowledge fills "doesn't know" but not "can't think"
- **Compilation × Distillation**: small model foundation (can think) + expert domain judgment (knows) = **small-model cost, with strong-model reasoning plus expert domain expertise**

Model vendors make "thinking" cheap (distillation); this repo makes "knowing" cheap (compilation). Together, a task that needs a senior expert can run on an open-source small model plus a knowledge pack — **10-100x cost difference**.

> Boundary: the combination applies to **knowledge-dense, reasoning-thin** tasks (evaluation, rule execution, process operation, QC judgment). Tasks requiring open-ended reasoning (creative planning, complex planning, long-chain reasoning) still need strong models.

---

## Core Insights

### 1. Inference Offloading
An expert's tacit knowledge → compiled into decision criteria, success/failure standards, and step-by-step if-then rules → **the agent only executes, never thinks**.
This is not "teaching" an agent; it's "reasoning for" the agent.

### 2. A Consumption Philosophy Designed for Weak Models
Mainstream knowledge frameworks (Claude Code skills, DSPy) target **flagship models**: knowledge is a "reference" and the model still thinks for itself.
This project is the **reverse design**: the knowledge framework's target consumer is a "dumb" model, so the structure must be foolproof —
**decision trees set direction, hard rules block errors, verified checklists remove reasoning, and the meta-skill enforces "just follow, don't think."**

### 3. Cost Arbitrage (Trade Document Complexity for Model Capability)
Because the knowledge pack is "dumb" enough and deterministic, weaker open-source models (10-100x cheaper) can do the same job.
**The more complete the knowledge → the less reasoning required → the cheaper the model you can use.**

---

## Three-Layer Meta-Skill System (Distill → Package → Compile)

```
knowledge-distillation   → Produce knowledge (thinker: analyze, verify, summarize, document pitfalls)
knowledge-packaging      → Package knowledge (organizer: structure into portable packs)
knowledge-compilation ★  → Consume knowledge (executor: just follow, don't think)
```

The first rule of compilation: **"Follow, Don't Think."** A knowledge pack is a verified conclusion; when consuming it, your only job is faithful execution, not re-verification. Be smart when *producing* knowledge (distillation), not when *consuming* it (execution).

### Why "Dumb" Is More Efficient

| Behavior | Result |
|---|---|
| Follow (dumb) | ✅ Reproduces verified success |
| Improvise (clever) | ❌ Breaks verified flows, hits new pitfalls |

A knowledge pack that a "dumb" agent can follow without error is the highest-quality deliverable.

---

## Knowledge Pack Structure (Five Layers)

A Compiled Knowledge Pack contains five layers:

```
SKILL.md        → decision tree (direction) + hard rules (constraints) + verified checklist
pipelines.md    → verified end-to-end pipelines
components.md   → reusable components (loops, templates, tools)
nodes.md        → measured values (parameter semantics, cross-system pitfalls, pitfalls log)
executable code → real scripts paired with the docs (tool layer)
```

See `runninghub-nodes/` (workflow node-editing knowledge pack) and `runninghub-web/` (web-operation knowledge pack, including a 25KB executable Python script).

---

## Innovation (The Combination Gap)

**All parts are public technology** — but the following end-to-end loop has no mature open-source implementation:

```
Use "successful experience" as ground truth to reverse-engineer private platform contracts
    → compile into deterministic knowledge packs (decision trees + hard rules + checklists)
    → inject at inference time into open-source small models (zero training cost)
    → validate transfer effects with statistical evaluation (knowledge density vs reasoning density)
```

Industry status quo:
- Anthropic/OpenAI skills systems: manuals are for **flagship models** (they assume you pay for the expensive ones)
- Open-source cost reduction: relies on **better reasoning / stronger models**, not better manuals
- Reverse engineering: done at the **code level** — nobody treats "working workflows" as documentation to reverse

**"Successful cases as ground truth, compile deterministic manuals, push the reasoning burden onto open-source models" — this combination is a gap.**

---

## Repository Contents

```
knowledge-compilation/     Compilation meta-skill (first rule for consuming knowledge)
knowledge-distillation/    Distillation meta-skill (producing knowledge)
knowledge-packaging/       Packaging meta-skill (packaging knowledge)
runninghub-nodes/          Compiled Knowledge Pack ①: RunningHub workflow node editing
runninghub-web/            Compiled Knowledge Pack ②: RunningHub web operation (with executable script)
agent-architecture.md      Knowledge Compilation architecture design document
```

---

## Roadmap

- [x] Knowledge Compilation methodology + two Compiled Knowledge Packs (nodes / web)
- [ ] **Controlled experiment**: same task, weak model + knowledge pack vs strong model bare — quantify "cost difference vs quality difference"
- [ ] **Statistical validation framework**: knowledge density vs reasoning density → decide what should be compiled; verify transfer effects statistically
- [ ] **Third Knowledge Pack**: cover a new domain to prove the methodology is reproducible

---

## License

MIT
