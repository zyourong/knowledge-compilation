---
name: knowledge-packaging
description: Package a completed, verified specialized capability (e.g. web operation, automation flows, platform integration) into a portable knowledge pack. Use when the user asks to "organize a skill/capability into transferable knowledge", "migrate to another agent", or "be able to follow the same approach next time". Reference case: knowledge/runninghub-web (RunningHub web-operation packaging).
---

# Knowledge Packaging Process

> **Purpose**: turn "a completed, real-world-verified specialized capability" into a **self-contained knowledge pack** that any agent (including weak-reasoning ones) can pick up and use.
> **Core principle**: write documentation until "a dumb agent following along can't go wrong" — every step has a decision criterion, success/failure standards, and verifiable output.

---

## 1. Input Check (before packaging)

| Check | Method | What if not satisfied |
|---|---|---|
| Capability verified in practice | The capability has real successful run records | Run it through first; never package a half-finished product |
| Core code exists | Has inspectable implementation files (Python/TS/scripts) | Write the code first |
| "Pitfalls hit" records exist | Problems encountered and solved in real use | Reconstruct the process and write the pitfalls (most valuable) |

**Content of a pack = code + strategy + measured conclusions + pitfall records** — all required.

---

## 2. Knowledge Pack Location and Structure

```
knowledge/{capability}/
├── README.md          ← migration guide (how to use, dependencies, verification)
├── SKILL.md           ← skill body (strategy layer: the agent reads this to know what to do)
├── EXTENSION.md       ← architecture summary (tool↔command mapping, implementation principles, migration guide)
├── {core code files}  ← code copies (rh_browser.py etc., inspectable)
└── examples/          ← correct examples (JSON modification samples, etc.)
```

**Naming**: create a directory per capability under `knowledge/`, lowercase with hyphens.

---

## 3. Writing the 5 Files

### 3.1 README.md (migration guide) — for "the person moving it"

Must include:
1. **Knowledge pack structure** (what each file does)
2. **5 migration steps**: which files to carry → install dependencies → first-time config (e.g. login) → register the capability → verification loop
3. **Core fact quick-reference** (measured conclusions, so readers don't re-hit pitfalls):
   - URLs, button texts, hidden iframes, state-detection logic
   - Where errors are displayed
4. **Command overview table** (what each command does)
5. **Common pitfalls list** (already hit, with symptoms and fixes)

### 3.2 SKILL.md (skill body) — for "the agent doing the work"

**The most important file — write it in most detail.** Structure:
1. **frontmatter**: `name` + `description` (description must state clearly "when to use")
2. **Prerequisite check table**: each check + what to do if not satisfied
3. **Key URL/resource quick-reference**
4. **Standard operation flows**: organized by scenario (A explore / B open / C run / D read errors / E extract results / F change config & re-run)
   - **Every scenario must have**:
     - concrete commands
     - numbered step sequence
     - ✅ success criterion / ❌ failure criterion
     - how to avoid common pitfalls
5. **Domain knowledge** (JSON structure, key rules, real cases)
6. **Hard rules** (rules whose violation breaks things, numbered)
7. **Pitfall log table** (pitfall | symptom | fix)
8. **Verification checklist** (post-operation self-check checkboxes)

**Writing requirements**:
- Steps detailed to "do X first, look at the result, if Y then do Z"
- Don't rely on reader reasoning — write out everything that seems "obvious"
- Give real command examples, never pseudocode

### 3.3 EXTENSION.md (architecture summary) — for "the person porting it"

1. **Architecture layering diagram** (strategy layer / wrapper layer / implementation layer)
2. **Tool ↔ command mapping table** (how each tool is invoked)
3. **Implementation principles** (how core functions work, e.g. the forwarding function)
4. **Core implementation points** (details that must not be lost when migrating, e.g. login-state persistence, hidden input injection)
5. **Environment dependencies**
6. **3 migration scenarios to other agents**:
   - Supports custom tools (pi) → register tools
   - bash only → call commands directly
   - Non-Python → port the logic

### 3.4 Code copies

- Copy core implementation files into the pack (keep consistent with the runtime environment)
- **After changing code, must sync the copy** (overwrite with `cp`)

### 3.5 examples/ (correct examples)

- Put "correct approach" instance files (e.g. a fixed JSON)
- **Must use the correct method**: if a wrong approach was discovered midway, write the "wrong vs right" comparison into SKILL.md — but examples only contain the right ones

---

## 4. Sync to the pi Skills Directory

After writing the pack, **sync to the location pi actually loads**:

```bash
cp knowledge/{capability}/SKILL.md .pi/skills/{capability}/SKILL.md
```

- `.pi/skills/` is the directory where pi auto-discovers skills
- **Must stay consistent**: re-cp after changing the pack

---

## 5. Verification (required after packaging)

| Verification | Command | Pass criterion |
|---|---|---|
| Code syntax | `python -m py_compile {code file}` | No errors |
| Copy consistency | `diff -q knowledge/{capability}/{code} .pi/scripts/{code}` | No differences |
| Doc consistency | `diff -q knowledge/{capability}/SKILL.md .pi/skills/{capability}/SKILL.md` | No differences |
| pi loads it | `pi -p "回复：正常"` | Normal reply, no extension errors |
| Pack structure | `find knowledge/{capability} -type f` | All 5 file types present |

---

## 6. Most Common Packaging Mistakes (self-check)

| # | Mistake | Correct approach |
|---|---|---|
| 1 | Docs too terse, relying on reader reasoning | Write until "a dumb agent following along can't go wrong"; give decision criteria at every step |
| 2 | Only packaging code, not the "measured pitfalls" | Pitfall records are the highest-value asset; must be included |
| 3 | Steps use "pseudocode/abstract descriptions" | Give real commands and real output examples |
| 4 | Conceptual confusion (e.g. "disable = disconnect") | After finding a conceptual error, write the "wrong vs right" comparison in SKILL.md |
| 5 | Forgetting to sync the pack copy after code changes | `cp` sync immediately after every code change |
| 6 | examples containing wrong approaches | examples only contain correct instances |

---

## 7. Reference Case (the RunningHub packaging)

**Completed pack**: `knowledge/runninghub-web/`
- README.md → SKILL.md → EXTENSION.md → rh_browser.py → rh-browser.ts → examples/lora_fixed_0.9_mode.json

**Key pitfalls hit at the time** (written into the docs):
1. Errors appear in the iframe, not the outer page
2. Task-status detection must filter by the latest taskid (historical failed tasks interfere)
3. "Disable ≠ disconnect": disable a node with mode=4 (mute), not by deleting links
4. The run button takes 20-30 seconds to appear; poll and wait

When facing a new "packaging knowledge" task, first read `knowledge/runninghub-web/` as a reference case, then follow this skill's process.

## Verification Checklist

- [ ] Input check passed (capability verified, code exists)?
- [ ] Pack directory structure complete (5 file types)?
- [ ] README has migration steps + core fact table + common pitfalls?
- [ ] SKILL.md has ✅/❌ criteria + real commands for every scenario?
- [ ] EXTENSION.md has tool↔command mapping + 3-scenario migration guide?
- [ ] Code copy synced and syntactically correct?
- [ ] examples contains only correct approaches?
- [ ] Synced to .pi/skills/ and consistent with the pack?
- [ ] pi load verification passed?
