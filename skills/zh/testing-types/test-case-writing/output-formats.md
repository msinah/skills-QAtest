# 输出格式说明

本技能默认输出为 **Markdown**。若需要 **Excel**、**CSV** 或 **JSON**，请在向 AI 提交需求时**在末尾明确说明**。

- **Excel**：在末尾加「请以 Excel 可粘贴的制表符分隔表格输出」。
- **CSV**：在末尾加「请以 CSV 格式（逗号分隔，首行为表头）输出」。
- **JSON**：在末尾加「请以 JSON 形式输出」。
- **可编辑 XMind**：在末尾加「请交付可编辑的 `.xmind` 文件」，并提供同事要求的字段/分组/排序格式（或示例文件）。按 `references/xmind-export.md` 调用 `scripts/export_xmind.py`；Skill 已附带空白模板。脚本生成的文件仍需在目标客户端打开验证。

详见仓库 `skills/testing-types/_output-formats-template-zh.md`。
