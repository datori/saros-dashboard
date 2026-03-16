---
name: "OPSX: Patch"
description: Explore, implement, and update specs directly — skipping the full change pipeline. For small tweaks and fixes.
category: Workflow
tags: [workflow, patch, experimental, quick]
---

Quick patch workflow: explore relevant specs → implement directly → update main specs in-place. No change artifacts created.

**Use this when**: The change is small enough that the full pipeline (ff → apply → archive) would be more overhead than value. Bug fixes, small tweaks, config changes, minor spec corrections.

**Use the full pipeline instead when**: The change is non-trivial, touches multiple capabilities, needs a design doc, or you want a paper trail.

**Input**: The argument after `/opsx:patch` describes what to patch (e.g., `/opsx:patch fix quota widget refresh loop`). If omitted, ask what needs patching.

---

## Steps

### 1. Clarify intent (if needed)

If no input was given, use **AskUserQuestion** to ask:
> "What do you want to patch? Describe the fix or change."

If the input is clear, proceed.

### 2. Survey relevant context

Run a quick scan to orient yourself:

```bash
openspec list --json
```

Check if there are active changes related to this patch. If so, mention them — the user may want to use the full pipeline instead.

Then read the specs most relevant to the described patch:
- Scan `openspec/specs/` for capability specs that may be affected
- Read those spec files for context
- Read any relevant source files to understand current behavior

**Keep this light.** This is not a deep exploration. Spend just enough time to understand what needs to change.

### 3. Confirm scope

Briefly describe to the user:
- What you understand needs to change
- Which main specs (if any) will need updating
- Roughly what the code change involves

If anything is ambiguous, ask before implementing.

### 4. Implement

Make the code changes directly. Keep them minimal and focused.

As you work:
- Note which specs will need updating to reflect what you've done
- Note any requirements that were actually changed vs. just clarified

### 5. Update main specs in-place

For each spec that needs updating, edit `openspec/specs/<capability>/spec.md` directly:

- **New behavior added** → add a requirement or scenario
- **Behavior changed** → update the existing requirement or scenario
- **Behavior removed** → remove the requirement
- **Spec was wrong/stale** → correct it

Apply the same intelligent-merging principle as `opsx:sync`:
- Add only what's new — don't rewrite the whole spec
- Preserve all content not affected by this patch
- Be surgical

If no spec updates are needed (e.g., it was a pure bug fix that doesn't change specified behavior), skip this step and say so.

### 6. Show summary

```
## Patch Complete

**What changed:**
- <brief description of code change>

**Specs updated:**
- openspec/specs/<capability>/spec.md — <what changed>

(Or: No spec updates needed — this was a behavior-preserving fix.)
```

---

## Guardrails

- **No change artifacts** — don't create `openspec/changes/<name>/` directories
- **Scope check** — if the patch is growing larger than expected, pause and suggest using the full pipeline
- **Don't over-spec** — only update specs when behavior genuinely changed or a spec was wrong
- **Minimal code changes** — stay focused on the described patch, don't refactor surrounding code
- **Pause on surprises** — if the codebase reveals something unexpected, surface it before proceeding
