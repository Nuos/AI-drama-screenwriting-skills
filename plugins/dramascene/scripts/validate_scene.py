#!/usr/bin/env python3
"""Structural and explicit-pattern lint only; not a semantic or video evaluator."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

CLASSICAL = re.compile(r"知否|海棠依旧|应是绿肥红瘦|奴家|何故|可曾知晓|甚好")
BAD_ACTION = re.compile(r"慢慢|缓缓|缓慢移动|缓慢走|低头凝视|垂眼|眼睑下垂|失神|叹气|郁闷|抑郁|眼神低落|凝视地面")


def validate(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    def require(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)
    def text(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())
    def strings(value: Any) -> bool:
        return isinstance(value, list) and all(text(x) for x in value)
    if not isinstance(data, dict):
        return {"ok": False, "errors": ["scene must be an object"], "warnings": [], "manual_review_required": True}
    require(data.get("schema_version") == "1.0", "unsupported schema_version")
    for key in ("title", "intent", "space"):
        require(text(data.get(key)), f"{key} must be nonempty text")
    source_kind = data.get("source_kind", "poem")
    require(source_kind in ("poem", "scene"), "invalid source_kind")
    structure = data.get("structure", {})
    if not isinstance(structure, dict):
        errors.append("structure must be an object")
        structure = {}
    mode = structure.get("mode")
    require(mode in ("spatial_coexistence", "inherited"), "invalid structure mode")
    require(text(structure.get("time_anchor")), "missing time_anchor")
    if mode == "spatial_coexistence":
        require(structure.get("reenact_past") is False, "spatial mode cannot reenact past events")
    characters = data.get("characters")
    if not strings(characters) or not characters:
        errors.append("characters must be a nonempty string array")
        characters = []
    require(len(characters) == len(set(characters)), "duplicate character")
    performance = data.get("performance", {})
    if not isinstance(performance, dict):
        errors.append("performance must be an object")
        performance = {}
    require(performance.get("pace") == "normal", "character pace must be normal")
    require(performance.get("affect") in ("calm_concern", "context_appropriate"), "invalid performance affect")
    require(performance.get("gaze") == "partner_or_task", "invalid gaze")
    policy = data.get("semantic_policy", {})
    if not isinstance(policy, dict):
        errors.append("semantic_policy must be an object")
        policy = {}
    require(data.get("manual_review_required") is True, "manual review must remain required")

    def records(key: str, allow_empty: bool = False) -> list[dict[str, Any]]:
        value = data.get(key)
        if not isinstance(value, list):
            errors.append(f"{key} must be an array")
            return []
        require(allow_empty or bool(value), f"{key} cannot be empty")
        result = []
        seen = set()
        for i, row in enumerate(value):
            if not isinstance(row, dict) or not text(row.get("id")):
                errors.append(f"{key}[{i}] needs an object and id")
                continue
            require(row["id"] not in seen, f"duplicate id in {key}: {row['id']}")
            seen.add(row["id"])
            result.append(row)
        return result
    units = records("source_units")
    dialogues = records("dialogues")
    voices = records("voiceovers", True)
    captions = records("poem_captions", source_kind == "scene")
    shots = records("shots")
    unit_map = {r["id"]: r for r in units}
    dialogue_map = {r["id"]: r for r in dialogues}
    voice_map = {r["id"]: r for r in voices}
    caption_map = {r["id"]: r for r in captions}
    shot_map = {r["id"]: r for r in shots}
    covered: set[str] = set()
    for row in units:
        require(text(row.get("text")) and text(row.get("meaning")), f"invalid source unit {row['id']}")
    originals = [u["text"] for u in units if text(u.get("text"))]
    if any("残酒" in s for s in originals):
        require(policy.get("residual_wine") == "intoxication", "residual wine must preserve intoxication")
    if any("应是" in s for s in originals):
        require(policy.get("inference") == "preserved", "source inference must be preserved")

    def refs(row: dict[str, Any], key: str, choices: dict[str, Any], nonempty: bool = False) -> list[str]:
        value = row.get(key)
        if not strings(value):
            errors.append(f"{row['id']}.{key} must be a string array")
            return []
        require(not nonempty or bool(value), f"{row['id']}.{key} cannot be empty")
        require(len(value) == len(set(value)), f"duplicate references: {row['id']}.{key}")
        for item in value:
            require(item in choices, f"unknown reference {row['id']}.{key}: {item}")
        return [x for x in value if x in choices]
    for row in dialogues + voices:
        require(text(row.get("text")), f"missing spoken text {row['id']}")
        spoken = row.get("text") if isinstance(row.get("text"), str) else ""
        require(not CLASSICAL.search(spoken), f"classical spoken line: {row['id']}")
        require(source_kind != "poem" or not any(len(s) >= 4 and s in spoken for s in originals), f"source verse used as speech: {row['id']}")
        covered.update(refs(row, "source_ids", unit_map, True))
    for row in dialogues:
        require(row.get("speaker") in characters, f"unknown speaker: {row['id']}")
    captioned = set()
    for row in captions:
        ids = refs(row, "source_ids", unit_map, True)
        captioned.update(ids)
        expected = "".join(unit_map[i].get("text", "") for i in ids if isinstance(unit_map[i].get("text"), str))
        require(row.get("channel") == "poem", f"wrong caption channel: {row['id']}")
        require(bool(expected) and row.get("text") == expected, f"changed source caption: {row['id']}")
    if source_kind == "poem":
        require(set(unit_map) <= captioned, "source units missing poem captions")
    used_d, used_n, used_t = set(), set(), set()
    moments = set()
    for row in shots:
        for key in ("framing", "camera", "action", "moment"):
            require(text(row.get(key)), f"{row['id']}.{key} must be nonempty text")
        if text(row.get("moment")):
            moments.add(row["moment"])
        kind = row.get("kind")
        require(kind in ("people", "object", "space"), f"invalid shot kind: {row['id']}")
        visible = row.get("visible_speakers")
        if not strings(visible):
            errors.append(f"invalid visible_speakers: {row['id']}")
            visible = []
        require(all(x in characters for x in visible), f"unknown visible character: {row['id']}")
        d = refs(row, "dialogue_ids", dialogue_map)
        n = refs(row, "voiceover_ids", voice_map)
        t = refs(row, "caption_ids", caption_map)
        covered.update(refs(row, "source_ids", unit_map, True))
        require(not (d and n), f"dialogue and narration overlap: {row['id']}")
        require(not (t and (d or n)), f"primary subtitle tracks overlap: {row['id']}")
        if d:
            require(kind == "people", f"dialogue over object or empty space: {row['id']}")
            if row.get("reaction_insert") is True:
                target_id = row.get("return_to", "")
                target = shot_map.get(target_id, {}) if isinstance(target_id, str) else {}
                target_visible = target.get("visible_speakers", [])
                target_visible = target_visible if strings(target_visible) else []
                require(all(i in used_d for i in d), f"dialogue must enter on speaker before reaction: {row['id']}")
                require(target.get("kind") == "people" and all(dialogue_map[i].get("speaker") in target_visible for i in d), f"reaction needs speaker return: {row['id']}")
            else:
                require(all(dialogue_map[i].get("speaker") in visible for i in d), f"speaker not visible: {row['id']}")
        action = row.get("action") if isinstance(row.get("action"), str) else ""
        require(not BAD_ACTION.search(action), f"explicit slow or depressed performance: {row['id']}")
        duration = row.get("duration_hint_s")
        good_duration = isinstance(duration, (int, float)) and not isinstance(duration, bool) and 0 < duration < float("inf")
        require(good_duration, f"invalid duration hint: {row['id']}")
        if good_duration and kind == "object" and duration > 3:
            warnings.append(f"review long object insert: {row['id']}")
        if good_duration and row.get("reaction_insert") is True and duration > 2:
            warnings.append(f"review long reaction insert: {row['id']}")
        used_d.update(d); used_n.update(n); used_t.update(t)
    require(set(unit_map) <= covered, "source units lack audiovisual coverage")
    require(set(dialogue_map) <= used_d, "unused dialogue")
    require(set(voice_map) <= used_n, "unused voiceover")
    require(set(caption_map) <= used_t, "unused poem caption")
    require(any(s.get("kind") in ("people", "space") for s in shots), "missing relational scene coverage")
    if mode == "spatial_coexistence":
        require(len(moments) == 1, "spatial mode requires one current moment")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "manual_review_required": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.scene.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2
    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
