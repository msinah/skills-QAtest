# Editable XMind Export

Export only when the user explicitly requests `.xmind`; otherwise retain the Skill's default Markdown output. Finish cross-source review, risk ranking, cases, and the traceability matrix first; then serialize the JSON input and run this Skill's `scripts/export_xmind.py`. The script, blank template, and standard-library-only implementation ship with this Skill.

## Template Requirements

- By default, use the sanitized team template at `output-templates/template-xmind.xmind`.
- For team-specific field names/order or grouping, declare ordered `fields` (`{ "key": "...", "label": "..." }`) and `groups` in the JSON. Use `--template` only when a specific topic style or page layout is required.
- The template must contain `content.json` as a non-empty top-level Sheet array whose first Sheet contains `rootTopic`.
- The exporter replaces the first Sheet's topic tree while preserving the other ZIP entries. It does not guess or mix package layouts from different XMind versions.
- Ask for a template only when a custom client layout is required and none was provided. Do not handcraft a package or rename `.xmind.md` to `.xmind`.

## JSON Input

```json
{
  "title": "Order test cases",
  "fields": [
    {"key": "case_id", "label": "Case ID"},
    {"key": "title", "label": "Case title"},
    {"key": "preconditions", "label": "Preconditions"},
    {"key": "steps", "label": "Steps"},
    {"key": "expected_result", "label": "Expected result"}
  ],
  "cases": [
    {
      "case_id": "TC-001",
      "title": "Submit an order successfully",
      "priority": "P0",
      "type": "positive",
      "trace": ["REQ-01"],
      "source_role": ["direct_input"],
      "preconditions": ["User is signed in"],
      "test_data": ["Valid product"],
      "steps": ["Open the order page", "Submit the order"],
      "expected_result": ["Order is created"],
      "notes": ""
    }
  ],
  "traceability": [
    {"trace": "REQ-01", "case_ids": ["TC-001"], "coverage_types": ["positive"], "gap": ""}
  ],
  "assumptions": []
}
```

`cases` is required and non-empty. `fields`, `traceability`, and `assumptions` are optional. Map a requested team schema to `fields` and use `groups` for custom names/order, for example `[{"title":"Login success","cases":[...]}]`; otherwise the exporter uses built-in fields and P0/P1/P2/P3 grouping. Each step becomes a child topic. Never invent missing case details.

## Run and Acceptance

```bash
python scripts/export_xmind.py --input cases.json --output cases.xmind --language en
```

Add `--template team-template.xmind` only for a required custom client layout. The script performs ZIP, JSON, and topic-tree preflight only. Report client acceptance only after opening the result in the target XMind client, confirming it displays without corruption and remains editable, preferably after save and reopen. Otherwise mark it “Pending target-client validation.”
