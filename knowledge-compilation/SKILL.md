---
name: knowledge-compilation
description: The compilation meta-skill: the first rule when using any verified knowledge pack — "Follow, Don't Think." When an agent is about to use runninghub-nodes / runninghub-web / any distilled knowledge pack, this skill defines how to consume knowledge correctly: don't re-reason, don't doubt verified conclusions, don't improvise on verified flows. Reference case: a merge workflow failed because of "cleverness" — image1/image2 were connected backwards.
---

# Knowledge Compilation

> **In one sentence**: a knowledge pack exists so you don't have to think. Follow it directly — that is the most efficient, most correct usage.
> **Core principle**: a knowledge pack = verified conclusions. When consuming it, your only job is **faithful execution**, not re-verification.

---

## 1. The First Rule: Follow, Don't Think

### Why "dumb" is more efficient

| Behavior | Result |
|---|---|
| Follow (dumb) | ✅ Reproduces verified success |
| Improvise (clever) | ❌ Breaks verified flows, hits new pitfalls |

**Cognitive inversion**: a knowledge pack that a "dumb" agent can follow without error is the highest-quality deliverable. Your intelligence belongs in **producing** knowledge packs (think clearly during distillation), not in **consuming** them (don't overthink during execution).

### 4 consumption guidelines

1. **Don't re-reason**: if the pack says "connect it this way," connect it that way. Don't "I think it should be..."
2. **Don't doubt verified conclusions**: measured values beat your intuition / official docs (e.g. AuraFlow 3.0 is not 1.73)
3. **Don't improvise**: don't "optimize" verified flows (e.g. running the three-view branch of grid tuning wastes resources)
4. **Check the pack first, then ask the user**: follow the pack if it has the answer; only ask if it doesn't

## 2. Origin of this meta-skill (real-world pitfall)

### Pitfall case: image1/image2 connected backwards

**Scenario**: merging character + clothing + try-on workflows into one.

**Wrong behavior**:
```
I "cleverly" re-analyzed the original workflows → connected by the original JSON slot numbers →
image1=clothing, image2=character → connected backwards
```

**Correct behavior (follow)**:
```
Read knowledge pack pipelines.md §5 → the hard rule clearly states image1=character image, image2=clothing image →
connect accordingly → correct
```

**Lesson**: don't override conclusions already summarized in the knowledge pack with "original JSON analysis." The original JSON is the raw material; the knowledge pack is the finished product — use the finished product.

## 3. Knowledge Compilation Consumption Protocol

```
1. Identify task type → match the corresponding knowledge pack (nodes/web/packaging/distillation)
2. Read SKILL.md's decision tree → determine which pipeline/component to use
3. Read the corresponding section → strictly follow wiring/parameters
4. No innovation during execution: only change "adjustable parameters", never touch "hard rules"
5. If the pack doesn't cover a case → stop and ask the user (don't guess)
6. After success → if there's new insight, write it back into the pack (the only allowed "innovation")
```

### Production vs consumption division (key)

| Phase | Your role | Behavior |
|---|---|---|
| **Distill / produce knowledge** | Thinker | Analyze, verify, summarize, document pitfalls |
| **Compile / consume knowledge** | Executor | Follow, don't doubt, only change adjustable items |

**Don't be a thinker during execution** — this is the biggest misconception in Knowledge Compilation.

## 4. Decision Guidelines (When to Follow vs When to Innovate)

| Situation | Behavior |
|---|---|
| Pack has a clear answer | **Follow** (100% execution) |
| Pack marks "adjustable" | May change (within safe range) |
| Pack marks "hard rule / don't reverse / don't delete" | **Absolutely do not change** |
| Pack doesn't cover it | **Ask the user** (don't guess, don't invent) |
| New pitfall found after success | **Write it back into the pack** (this is distillation — the innovation phase) |

## 5. Relationship with Other Meta-Skills

```
knowledge-distillation → produce knowledge (thinker role)
knowledge-packaging    → package knowledge (organizer role)
knowledge-compilation  → consume knowledge (executor role) ★ first rule when using knowledge
```

The closed loop: **distill → package → compile**. This skill is the executor-side meta-skill.

## 6. Verification Checklist (self-check after each consumption)

- [ ] Did I follow the pack's conclusions directly instead of re-reasoning?
- [ ] Did I NOT "optimize" verified flows?
- [ ] Did I only change parameters marked "adjustable"?
- [ ] When the pack didn't cover a case, did I ask the user instead of guessing?
- [ ] If there was a new pitfall, did I write it back into the pack?
