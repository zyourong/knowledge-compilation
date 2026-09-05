---
name: knowledge-distillation
description: Extract structured knowledge from raw data / real-world practice records (knowledge distillation). Use when the user asks to "summarize rules from a pile of successful workflows/data", "extract a platform's node/operation contracts into reusable knowledge", or "be able to follow the same approach next time". Difference from knowledge-packaging: packaging turns "an existing capability" into a portable format; distillation derives "knowledge that didn't exist before" from "raw data". Reference case: knowledge/runninghub-nodes (node-editing knowledge distilled from 6 workflow JSONs).
---

# Knowledge Distillation Process

> **Purpose**: extract **structured domain knowledge** from raw data (successful cases, workflow JSONs, operation logs), so agents don't have to re-discover it next time.
> **Core principle**: knowledge must come from **verified ground truth** (cases that actually ran successfully), and the structure must be **minimal** — distill, don't copy.
> **Division of labor with packaging**: packaging handles "existing capability → portable pack"; distillation handles "raw data → domain knowledge".

---

## 1. Input Check (before distilling)

| Check | Method | What if not satisfied |
|---|---|---|
| Multiple success samples | At least 2 verified cases (more samples → clearer patterns) | Run more cases first; don't over-generalize from a single case |
| Samples are parseable | Structure can be read (JSON/logs/records) | Write a parsing script first |
| Failure records exist | Pitfalls hit during successful runs | Reconstruct them (pitfalls are the most valuable distillation output) |

**Input to distillation = raw data + real-world experience** — both are required.

---

## 2. The Five-Step Distillation Method (from data to knowledge)

### Step 1: Statistical inventory (see the whole picture first, don't classify yet)

- Count **type + frequency** of all entities in the samples (e.g. node type distribution)
- Identify high-frequency entities vs one-off entities (high-frequency = core, one-off = edge)

### Step 2: Extract topology (who connects to whom; chains before nodes)

- Analyze **connections** rather than isolated entities: each entity's input sources / output destinations
- Key conclusion: **entities don't exist independently** — they only make sense assembled into chains
- Find recurring "chain fragments" (= candidate components)

### Step 3: Identify systems (cluster by "capability/ecosystem", not by task)

- Find **ecosystem units** in the samples: each unit = one bound set of components
  - e.g. base model → its dedicated CLIP/VAE/sampler/ControlNet/LoRA
- **Classify systems by capability** (edit/generate/guide), **not by task**
- ⚠️ Most common mistake: writing "verified scenario" as "the only use" (see §6 #1)

### Step 4: Distill components (public modules reusable across systems)

- On top of systems, find **cross-system reusable** process modules
- For each component record: function + node composition + wiring points (where it connects) + verified source

### Step 5: Define boundaries (hard rules = safe red lines)

- Extract "what must not be done" from pitfalls (cross-system mixing, unverified combinations, parameter order)
- Hard rules are the negative space of knowledge — without them, agents invent dangerous combinations

---

## 3. Minimal Structure (organizing distillation output)

**Core principle: knowledge packs store only distilled knowledge; raw data is not copied — read the original files when needed.**

```
knowledge/{domain}/
├── SKILL.md        ← entry: decision tree + system table + hard rules + flows + verified checklist (one page)
├── {system}/wiring.md  ← system knowledge: ≤15 lines per system (dedicated components + wiring + adjustable params)
├── {component}/method.md ← component knowledge: ≤8 lines per component (function + wiring points + precedents)
└── {contract}/detail.md  ← contract library read on demand (parameter semantics + measured values)
```

**Size red line**: 4 files, 2-4K each. More = over-engineering (see §6 #2).

**Reference instead of copy**: when examples are needed, read the raw data files — don't copy them into the pack (avoids bloat + double maintenance).

---

## 4. Retrieval Design (knowledge is only useful if it can be found)

1. **Decision tree first**: SKILL.md starts with the "need → direction" decision tree (edit/generate/guide + subtasks)
2. **One-page orientation**: reading the entry file tells you exactly "which file, which section"
3. **Read on demand**: contract/detail files are only read when encountering unknown items
4. **Cross-references**: system table ↔ components ↔ contracts linked by section numbers

---

## 5. Distillation Validation Loop

Distilled knowledge **must guide real tasks** to count as valid:

```
Use distilled knowledge to do a new task
  → success: knowledge is valid (record as precedent)
  → failure: error → fix against the contract → re-run (stop after 2 consecutive failures)
  → new insights after fixing → write back into the pack (distillation value-add)
```

---

## 6. Most Common Distillation Mistakes (self-check)

| # | Mistake | Correct approach |
|---|---|---|
| 1 | Writing "verified scenario" as "the only use" | Write "capability essence + verified scenario (≠only)"; don't lock tasks to systems |
| 2 | Over-engineering: one file per entity, adding metadata/index/orchestration layers | Minimal 4 files; merge index/orchestration into SKILL.md's one page |
| 3 | Copying raw data into the pack | Reference original file paths, don't copy (avoids bloat + dual maintenance) |
| 4 | Classifying systems by task ("this model can only do X") | Classify by capability, mark verified scenarios |
| 5 | Only writing "how to connect", not "what must not be connected" | Hard rules must be distilled separately (pitfall experience is the most valuable) |
| 6 | Relying on reader reasoning ("obviously...") | Give decision criteria at every step; write until "a dumb agent following along can't go wrong" |

---

## 7. Reference Case (the RunningHub distillation)

**Output**: `knowledge/runninghub-nodes/` (4 files, 20K)
- Input: 6 workflow JSONs (character/scene/grid/prop/prompt/try-on)
- Distilled knowledge:
  - 4 base-model systems (Qwen-edit/Z-Image/FLUX.1/FLUX.2) — classified by capability
  - 6 cross-base-model components (grid tuning / dynamic prompts / dedup / sizing / routing / LLM flow)
  - 7 hard rules (LoRA cross-system / sampling binding / base model ≠ task-specific, etc.)
  - Node contracts (measured values beat official defaults)

**Key pitfalls hit at the time** (already written into the pack):
1. Wrote "verified scenario" as "the only use" (corrected by user; added hard rule "base model ≠ task-specific")
2. Initially built an inflated 19-file/184K structure (cut down to 4 files/20K after user correction)
3. Mislabeled ComfyUI official nodes as "RunningHub-private" (fixed source attribution after verifying source code)

When facing a new "knowledge distillation" task, first read `knowledge/runninghub-nodes/` as a reference case, then follow this skill's process.

## Verification Checklist

- [ ] Input check passed (multiple success samples, parseable, pitfall records)?
- [ ] Five steps completed (inventory → topology → systems → components → hard rules)?
- [ ] Systems classified by capability, marked "verified scenario ≠ only use"?
- [ ] Structure minimal (≤4 files, each ≤4K)?
- [ ] Raw data referenced, not copied?
- [ ] Decision tree first, one-page orientation?
- [ ] Hard rules distilled from pitfalls (not copied from docs)?
- [ ] A new task actually completed using the distilled knowledge?
- [ ] New insights written back into the pack (distillation value-add)?
