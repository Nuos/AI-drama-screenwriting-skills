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
    require(data.get("schema_version") in ("1.0", "1.1"), "unsupported schema_version")
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
        covered.update(refs(row, "source_ids", unit_map, data.get("schema_version") == "1.0"))
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
    if data.get("schema_version") == "1.1":
        validate_v11(data, errors, warnings)
    return {"ok": not errors, "errors": errors, "warnings": warnings, "manual_review_required": True}


def validate_v11(data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Validate declared contracts and explicit text patterns, not artistic quality."""
    def need(ok: bool, message: str) -> None:
        if not ok: errors.append(message)
    def text(v: Any) -> bool: return isinstance(v, str) and bool(v.strip())
    def items(v: Any) -> list[dict[str, Any]]:
        return [x for x in v if isinstance(x, dict) and text(x.get('id'))] if isinstance(v, list) else []
    def ids(v: Any, label: str) -> list[str]:
        if not isinstance(v, list) or not all(text(x) for x in v):
            errors.append(f'{label} must be a string array'); return []
        need(len(v) == len(set(v)), f'duplicate references: {label}')
        return v
    units = {x['id']: x for x in items(data.get('source_units'))}
    dialogue = {x['id']: x for x in items(data.get('dialogues'))}
    voices = items(data.get('voiceovers'))
    shots = items(data.get('shots'))
    def table(key: str, nonempty: bool = True) -> dict[str, dict[str, Any]]:
        raw = data.get(key)
        need(isinstance(raw, list), f'{key} must be an array')
        rows = items(raw)
        need(isinstance(raw, list) and len(rows) == len(raw), f'{key} rows need object and id')
        need(not nonempty or bool(rows), f'{key} cannot be empty')
        need(len(rows) == len({x['id'] for x in rows}), f'duplicate id in {key}')
        return {x['id']: x for x in rows}
    context = table('context_facts')
    for cid, row in context.items():
        need(text(row.get('text')), f'missing context text: {cid}')
        need(row.get('origin') in ('source_text', 'adaptation'), f'context origin invalid: {cid}')
        source_ids = ids(row.get('source_ids'), f'{cid}.source_ids')
        need(all(x in units for x in source_ids), f'unknown context source: {cid}')
        if row.get('origin') == 'source_text': need(bool(source_ids), f'source context needs evidence: {cid}')
    context_used_by_dialogue: set[str] = set()
    for row in list(dialogue.values()) + voices:
        context_ids = ids(row.get('context_ids'), f'{row["id"]}.context_ids')
        need(all(x in context for x in context_ids), f'unknown context reference: {row["id"]}')
        src = row.get('source_ids', [])
        need(bool(context_ids) or (isinstance(src, list) and bool(src)), f'speech needs source or context: {row["id"]}')
        if row['id'] in dialogue: context_used_by_dialogue.update(context_ids)
    order = ids(data.get('dialogue_order'), 'dialogue_order')
    need(set(order) == set(dialogue), 'dialogue_order must cover every dialogue exactly once')
    for i, did in enumerate(order):
        row = dialogue.get(did, {})
        need(row.get('reply_to') == (order[i-1] if i else None), f'broken dialogue continuation: {did}')
        need(text(row.get('speech_action')), f'missing speech_action: {did}')
    encountered = []
    for row in shots:
        for did in ids(row.get('dialogue_ids'), f'{row["id"]}.dialogue_ids'):
            if did not in encountered: encountered.append(did)
    need(encountered == order, 'shot dialogue order differs from conversation')
    setting = data.get('setting')
    if not isinstance(setting, dict):
        errors.append('setting must be an object'); setting = {}
    need(setting.get('mode') in ('outdoor_only', 'user_override'), 'invalid setting mode')
    if setting.get('mode') == 'user_override':
        need(text(setting.get('override_reason')), 'setting override needs explicit user reason')
    locations_raw = setting.get('locations')
    locations = items(locations_raw)
    need(isinstance(locations_raw, list) and len(locations_raw) == len(locations) and bool(locations), 'locations need nonempty valid rows')
    need(len(locations) == len({x['id'] for x in locations}), 'duplicate location id')
    location_ids = {x['id'] for x in locations}
    outdoor = setting.get('mode') == 'outdoor_only'
    indoor = re.compile(r'室内|屋内|房间内|卧室|厅内|门内|窗内|内景|走进屋|走进房|推入屋')
    if outdoor:
        need(setting.get('architecture_role') == 'background_prop_only', 'architecture must be background prop only')
        need(all(x.get('roof') == 'open_sky' for x in locations), 'all locations must have open sky')
        for row in locations:
            need(not indoor.search(str(row.get('description', ''))), f'indoor location description: {row["id"]}')
        need(not indoor.search(str(data.get('space', ''))), 'indoor master space')
        need(not indoor.search(str(setting.get('description', ''))), 'indoor setting description')
    for row in shots:
        need(isinstance(row.get('location_id'), str) and row['location_id'] in location_ids, f'unknown shot location: {row["id"]}')
        if outdoor:
            need(row.get('environment') == 'outdoor' and row.get('camera_environment') == 'outdoor', f'all shots and cameras must be outdoor: {row["id"]}')
            for key in ('action', 'camera', 'framing'):
                need(not indoor.search(str(row.get(key, ''))), f'indoor shot text: {row["id"]}.{key}')
    narrator_pattern = re.compile(r'不是[^。！？]*而是|不[^。！？]*还|这说明|由此可见|可以推断|这里的|她問的是|她问的是|他问的是|真正想|她(?:其实|心里)?(?:想要|希望|在意|猜测)|他(?:其实|心里)?(?:想要|希望|在意|猜测)')
    spoken_dialogue = [x.get('text') for x in dialogue.values()]
    for row in voices:
        need(row.get('function') in ('background', 'omitted_fact', 'world_rule'), f'narration must add background: {row["id"]}')
        value = row.get('text', '')
        need(isinstance(value, str) and not narrator_pattern.search(value), f'analytical or mind-reading narration: {row["id"]}')
        need(value not in spoken_dialogue, f'narration repeats dialogue: {row["id"]}')
        added = ids(row.get('added_context_ids'), f'{row["id"]}.added_context_ids')
        refs = ids(row.get('context_ids'), f'{row["id"]}.context_ids')
        need(bool(added) and all(x in context and x in refs for x in added), f'narration needs supported added information: {row["id"]}')
        need(bool(set(added) - context_used_by_dialogue), f'narration adds no new context: {row["id"]}')
    adaptation = data.get('adaptation_policy')
    if not isinstance(adaptation, dict):
        errors.append('adaptation_policy must be an object'); adaptation = {}
    need(isinstance(adaptation.get('allow_imagination'), bool), 'allow_imagination must be boolean')
    need(text(adaptation.get('note')), 'adaptation needs provenance note')
    effects = table('effects', False)
    if effects: need(adaptation.get('allow_imagination') is True, 'imagination needs authorization')
    effect_usage: dict[str, list[dict[str, Any]]] = {}
    for shot in shots:
        for eid in ids(shot.get('effect_ids'), f'{shot["id"]}.effect_ids'):
            need(eid in effects, f'unknown effect: {eid}')
            effect_usage.setdefault(eid, []).append(shot)
    for eid, row in effects.items():
        for key in ('visual', 'sound', 'music', 'return_rule'):
            need(text(row.get(key)), f'effect needs {key}: {eid}')
        need(row.get('reality_layer') == 'expressive', f'effect must declare expressive layer: {eid}')
        if isinstance(data.get('structure'), dict) and data['structure'].get('mode') == 'spatial_coexistence':
            need(row.get('time_mode') == 'concurrent_expression', f'effect cannot reenact past: {eid}')
        source_ids = ids(row.get('source_ids'), f'{eid}.source_ids')
        need(bool(source_ids) and all(x in units for x in source_ids), f'effect needs source coverage: {eid}')
        trigger = row.get('trigger_dialogue_id')
        need(isinstance(trigger, str) and trigger in dialogue, f'effect trigger invalid: {eid}')
        need(eid in effect_usage, f'unused effect: {eid}')
        need(any(isinstance(x.get('dialogue_ids'), list) and trigger in x['dialogue_ids'] for x in effect_usage.get(eid, [])), f'effect missing trigger shot: {eid}')
    # Keyword and metadata checks intentionally leave all artistic judgments to review.


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
