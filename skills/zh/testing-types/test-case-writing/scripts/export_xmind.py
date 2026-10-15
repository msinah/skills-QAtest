#!/usr/bin/env python3
"""Export structured test cases into a client-template-based XMind package."""
import argparse
import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any


FIELDS = [
    ("Case ID", ("case_id", "id")),
    ("Priority", ("priority",)),
    ("Type", ("type",)),
    ("Trace", ("trace",)),
    ("Source role", ("source_role",)),
    ("Preconditions", ("preconditions", "precondition")),
    ("Test data", ("test_data", "data")),
    ("Steps", ("steps",)),
    ("Expected result", ("expected_result", "expected")),
    ("Notes", ("notes", "remark")),
]
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / "output-templates" / "template-xmind.xmind"


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _field(case: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        if key in case:
            return case[key]
    return ""


def _topic(title: str, children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    node: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "title": title,
        "titleUnedited": title,
    }
    if children is not None:
        node["children"] = {"attached": children}
    return node


def _case_topic(
    case: dict[str, Any],
    language: str,
    field_specs: list[dict[str, str]] | None,
    layout: str,
) -> dict[str, Any]:
    title = _text(_field(case, ("title",))) or "Untitled test case"
    case_id = _text(_field(case, ("case_id", "id")))
    if case_id and layout == "detailed":
        title = f"{case_id} | {title}"
    aliases_by_key = dict(FIELDS)
    default_labels = {
        "case_id": "用例 ID", "priority": "优先级", "type": "类型", "trace": "需求追踪",
        "source_role": "来源角色", "preconditions": "前置条件", "test_data": "测试数据",
        "steps": "测试步骤", "expected_result": "预期结果", "notes": "备注",
    }
    if field_specs is not None:
        specs = field_specs
    elif layout == "test-points":
        specs = [
            {"key": "steps", "label": "Steps" if language == "en" else "操作步骤"},
            {"key": "expected_result", "label": "Expected result" if language == "en" else "预期结果"},
        ]
    else:
        specs = [
            {"key": aliases[0], "label": (label if language == "en" else default_labels.get(aliases[0], label))}
            for label, aliases in FIELDS
        ]
    details = []
    for spec in specs:
        key = spec["key"]
        label = spec.get("label", key)
        aliases = aliases_by_key.get(key, (key,))
        value = _text(_field(case, aliases))
        if not value:
            continue
        if key == "steps":
            raw_steps = _field(case, aliases)
            steps = raw_steps if isinstance(raw_steps, list) else [raw_steps]
            detail_children = [_topic(f"{index}. {_text(step)}") for index, step in enumerate(steps, 1) if _text(step)]
            details.append(_topic(label, detail_children))
        else:
            details.append(_topic(f"{label}: {value}"))
    return _topic(title, details)


def _case_groups(payload: dict[str, Any], language: str) -> list[dict[str, Any]]:
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Input JSON must contain a non-empty 'cases' array.")
    explicit_groups = payload.get("groups")
    if isinstance(explicit_groups, list) and explicit_groups:
        case_by_id = {
            _text(_field(case, ("case_id", "id"))): case
            for case in cases
            if isinstance(case, dict) and _text(_field(case, ("case_id", "id")))
        }
        groups = []
        for group in explicit_groups:
            if not isinstance(group, dict):
                raise ValueError("Each item in 'groups' must be an object.")
            group_cases = group.get("cases")
            if group_cases is None and "case_ids" in group:
                case_ids = group["case_ids"]
                if not isinstance(case_ids, list):
                    raise ValueError("'case_ids' in a group must be an array.")
                missing = [case_id for case_id in case_ids if _text(case_id) not in case_by_id]
                if missing:
                    raise ValueError(f"Unknown case IDs in group: {', '.join(_text(item) for item in missing)}")
                group_cases = [case_by_id[_text(case_id)] for case_id in case_ids]
            if not isinstance(group_cases, list):
                raise ValueError("Each group must contain a 'cases' or 'case_ids' array.")
            groups.append({"title": group.get("title"), "cases": group_cases})
    else:
        priorities = ("P0", "P1", "P2", "P3", "Unprioritized")
        by_priority: dict[str, list[dict[str, Any]]] = {key: [] for key in priorities}
        for case in cases:
            priority = _text(case.get("priority")).upper()
            by_priority[priority if priority in by_priority else "Unprioritized"].append(case)
        groups = [
            {"title": key, "cases": values}
            for key, values in by_priority.items()
            if values
        ]
    labels = {
        "zh": {"Cases": "测试用例"},
        "en": {"Cases": "Test cases"},
    }[language]
    field_specs = payload.get("fields")
    if field_specs is not None and (
        not isinstance(field_specs, list)
        or any(not isinstance(item, dict) or not isinstance(item.get("key"), str) for item in field_specs)
    ):
        raise ValueError("'fields' must be an ordered array of objects with a string 'key'.")
    layout = payload.get("layout", "detailed")
    if layout not in ("detailed", "test-points"):
        raise ValueError("'layout' must be either 'detailed' or 'test-points'.")
    return [
        _topic(
            _text(group.get("title")) or labels["Cases"],
            [_case_topic(case, language, field_specs, layout) for case in group.get("cases", [])],
        )
        for group in groups
    ]


def _content_tree(payload: dict[str, Any], template_content: bytes, language: str) -> bytes:
    sheets = json.loads(template_content.decode("utf-8"))
    if not isinstance(sheets, list) or not sheets:
        raise ValueError("Template content.json must be a non-empty Sheet array.")
    sheet = sheets[0]
    if not isinstance(sheet, dict) or not isinstance(sheet.get("rootTopic"), dict):
        raise ValueError("The first template Sheet must contain a rootTopic object.")

    branches = _case_groups(payload, language)
    layout = payload.get("layout", "detailed")
    include_supporting = payload.get("include_supporting_sections", layout == "detailed")
    if not isinstance(include_supporting, bool):
        raise ValueError("'include_supporting_sections' must be a boolean.")
    if include_supporting and payload.get("traceability"):
        links = []
        for item in payload["traceability"]:
            if isinstance(item, dict):
                trace = _text(item.get("trace") or item.get("requirement") or item.get("risk"))
                case_ids = _text(item.get("case_ids") or item.get("cases"))
                note = _text(item.get("gap") or item.get("note"))
                parts = [part for part in (case_ids, note) if part]
                links.append(_topic(f"{trace}: {'; '.join(parts)}" if parts else trace))
            else:
                links.append(_topic(_text(item)))
        branches.append(_topic("追踪矩阵" if language == "zh" else "Traceability matrix", links))
    if include_supporting and payload.get("assumptions"):
        assumptions = payload["assumptions"]
        if not isinstance(assumptions, list):
            assumptions = [assumptions]
        branches.append(_topic(
            "假设与缺口" if language == "zh" else "Assumptions and gaps",
            [_topic(_text(item)) for item in assumptions if _text(item)],
        ))

    root = sheet["rootTopic"]
    root["title"] = _text(payload.get("title")) or root.get("title") or "Test cases"
    root["titleUnedited"] = root["title"]
    children = root.get("children")
    if not isinstance(children, dict):
        children = {}
        root["children"] = children
    children["attached"] = branches
    return json.dumps(sheets, ensure_ascii=False, indent=2).encode("utf-8")


def export(payload_path: Path, template_path: Path, output_path: Path, language: str) -> None:
    if payload_path.resolve() == output_path.resolve() or template_path.resolve() == output_path.resolve():
        raise ValueError("Output must be a different file from the input and template.")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object.")
    with zipfile.ZipFile(template_path, "r") as source:
        names = source.namelist()
        if "content.json" not in names:
            raise ValueError("Template must contain content.json; create it with the target XMind client.")
        replacement = _content_tree(payload, source.read("content.json"), language)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(temp_name, "w") as target:
                for info in source.infolist():
                    data = replacement if info.filename == "content.json" else source.read(info.filename)
                    target.writestr(info, data)
            with zipfile.ZipFile(temp_name, "r") as check:
                if check.testzip() is not None:
                    raise ValueError("Output package failed ZIP integrity validation.")
                parsed = json.loads(check.read("content.json").decode("utf-8"))
                if not isinstance(parsed, list) or not parsed[0]["rootTopic"].get("children", {}).get("attached"):
                    raise ValueError("Output content tree failed structural validation.")
            os.replace(temp_name, output_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Structured test case JSON")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Optional team XMind template; defaults to the bundled blank template")
    parser.add_argument("--output", required=True, type=Path, help="Output .xmind path")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    args = parser.parse_args()
    export(args.input, args.template, args.output, args.language)
    print(args.output)


if __name__ == "__main__":
    main()
