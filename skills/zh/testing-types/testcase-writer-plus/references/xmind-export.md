# 可编辑 XMind 导出

只有用户明确要求 `.xmind` 时才执行导出；未指定时保持本 Skill 的 Markdown 默认输出。先完成多源核对、风险分级、用例和追踪矩阵，再生成 JSON 临时输入并运行本 Skill 自带的 `scripts/export_xmind.py`。脚本、空白模板和标准库依赖均随 Skill 一起分发。

## 模板要求

- 默认使用 `output-templates/template-xmind.xmind`，该模板由团队 XMind 样例脱敏后随 Skill 提供。
- 同事要求不同字段、字段顺序或分组时，在 JSON 中用 `fields`（按顺序排列 `{ "key": "...", "label": "..." }`）和 `groups` 描述；只有要求特定主题样式/页面布局时，才通过 `--template` 指定目标 XMind 客户端创建的模板。
- 模板必须含 `content.json`，且其顶层是非空 Sheet 数组，首个 Sheet 含 `rootTopic`。
- 导出器以模板为基础替换首个 Sheet 的主题树，并保留其他 ZIP 包条目；它不猜测或混合不同 XMind 版本的包格式。
- 需要自定义模板但用户未提供时才询问；不要自行拼装 XMind 包，也不要把 `.xmind.md` 改名成 `.xmind`。

## JSON 输入

```json
{
  "title": "订单测试用例",
  "fields": [
    {"key": "case_id", "label": "用例编号"},
    {"key": "title", "label": "用例标题"},
    {"key": "preconditions", "label": "前置条件"},
    {"key": "steps", "label": "操作步骤"},
    {"key": "expected_result", "label": "预期结果"}
  ],
  "cases": [
    {
      "case_id": "TC-001",
      "title": "成功提交订单",
      "priority": "P0",
      "type": "正向",
      "trace": ["REQ-01"],
      "source_role": ["direct_input"],
      "preconditions": ["用户已登录"],
      "test_data": ["有效商品"],
      "steps": ["打开订单页", "提交订单"],
      "expected_result": ["订单创建成功"],
      "notes": ""
    }
  ],
  "traceability": [
    {"trace": "REQ-01", "case_ids": ["TC-001"], "coverage_types": ["正向"], "gap": ""}
  ],
  "assumptions": []
}
```

`cases` 必须非空。`fields` 可选；省略时使用内置字段。用户给出团队格式时，将字段名/顺序映射到 `fields`，并按要求用 `groups` 定义分组，例如 `[{"title":"登录成功","cases":[...]}]`；否则按 P0、P1、P2、P3 分组。步骤会逐项成为子主题。缺失字段不得编造。

## 调用与验收

```bash
python scripts/export_xmind.py --input cases.json --output cases.xmind --language zh
```

如需特定客户端模板，可追加 `--template team-template.xmind`。脚本仅做 ZIP、JSON 和主题树结构预检。只有目标 XMind 客户端实际打开、无损显示并可编辑，最好保存后重新打开，才可报告客户端验收通过；否则标记为“待用户客户端验证”。
