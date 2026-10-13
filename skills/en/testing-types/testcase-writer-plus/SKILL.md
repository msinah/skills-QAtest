---
name: testcase-writer-plus
description: Use this skill when you need high-quality test cases from requirements and analysis artifacts; triggers include testcase writer plus and advanced test case writing.
---

# testcase-writer-plus (EN)

**Chinese version：** See the corresponding Chinese skill.

## When to Use

- Need test cases from multiple source documents with stronger prioritization.
- Need better traceability and clearer risk focus than the base version.

## Workflow

1. Read and follow the main prompt listed under Progressive disclosure (coverage, structure, quality bar).
2. Add only project context that changes the result: scope, environment, constraints, risks, dependencies, expected deliverable.
3. If input is incomplete, return a usable first draft and explicitly mark assumptions and gaps.
4. Default to Markdown; switch formats only when the user asks.

## Core Constraints

- Prioritize by risk / business impact — do not treat everything equally.
- Separate confirmed facts from current assumptions.
- Do not invent endpoints, fields, environments, or root causes the user did not provide.
- Keep output executable: concrete scenarios, clear priority, clear next steps.

## Progressive Disclosure

- Before producing output, read and follow `prompts/testcase-writer-plus.md` (minimum coverage, output structure, quality bar).
- Only when `.xmind` is explicitly requested: read `references/xmind-export.md`, shape cases to the user's/team's requested fields while retaining priority groups, traceability, and assumptions, then run `scripts/export_xmind.py`. A sanitized blank template is bundled with this Skill; no extra dependency or template request is needed. If no format is specified, keep the default Markdown output and do not generate another file.
- When a ready-made template fits: use matching files under `output-templates/`.
- When the user wants examples or alignment with existing assets: read relevant `examples/`.
- For deep framework/troubleshoot/schema notes: read only the relevant file(s) under `references/`, do not load the whole directory.
- For format conversion or helper checks: prefer existing `scripts/` over reinventing.
- For evaluating/regressing this skill: use `evals/` with skill-up.

## Pre-delivery Checklist

- [ ] Followed the main prompt's output structure
- [ ] Minimum coverage focus: scope, priority grouping, traceability, preconditions, test data, positive scenarios, negative scenarios, boundary scenarios, ... (details in main prompt)
- [ ] Covered the minimum checklist, or explained omissions
- [ ] High-risk items have explicit priority
- [ ] Did not invent details the user did not provide
- [ ] Assumptions and gaps are marked
- [ ] For XMind requests, deliver a `.xmind` package and do not treat structural preflight as target-client acceptance

## Common Pitfalls

- Do not pretend completeness when scope/context is missing.
- Do not treat every item as equally important.
- Do not skip assumptions and information gaps.
- Do not dump generic theory unrelated to the current toolchain.
