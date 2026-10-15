# Output Format Options

This skill **defaults to Markdown**. To get **Excel**, **CSV**, or **JSON**, add at the **end** of your request:

- **Excel:** "Please output as tab-separated table for pasting into Excel."
- **CSV:** "Please output as CSV (comma-separated, header row first)."
- **JSON:** "Please output as JSON."
- **Editable XMind:** "Please deliver an editable `.xmind` file using these team fields/order/grouping: ..." Follow `references/xmind-export.md` and run `scripts/export_xmind.py`; a sanitized blank template is bundled with this Skill. The generated package still needs to be opened and checked in the target client.
- **Concise test-point XMind:** "Please use the concise test-point XMind layout." Export with `layout: "test-points"`; the main tree shows only modules, test points, steps, and expected results. Do not enable this layout unless requested.

See repo `skills/testing-types/_output-formats-template-en.md` for examples.
