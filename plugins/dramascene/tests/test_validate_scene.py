"""Positive and negative regression fixtures. No external services or media."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_scene.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = json.loads((ROOT / "examples/lianwai/scene.json").read_text(encoding="utf-8"))

class SceneTests(unittest.TestCase):
    def setUp(self): self.scene = copy.deepcopy(BASE)
    def reject(self, snippet):
        result = module.validate(self.scene)
        self.assertFalse(result["ok"], result)
        self.assertTrue(any(snippet in x for x in result["errors"]), result)
    def test_baseline(self):
        self.assertEqual(module.validate(BASE), {"ok": True, "errors": [], "warnings": [], "manual_review_required": True})
    def test_non_object(self): self.assertFalse(module.validate(None)["ok"])
    def test_missing_intent(self):
        del self.scene["intent"]; self.reject("intent")
    def test_bad_structure(self):
        self.scene["structure"] = []; self.reject("structure")
    def test_bad_characters(self):
        self.scene["characters"] = [{}]; self.reject("characters")
    def test_past_reenactment(self):
        self.scene["structure"]["reenact_past"] = True; self.reject("reenact")
    def test_multiple_moments(self):
        self.scene["shots"][0]["moment"] = "last night"; self.reject("one current")
    def test_inherited_structure(self):
        self.scene["structure"]["mode"] = "inherited"
        self.scene["shots"][0]["moment"] = "other time"
        self.assertTrue(module.validate(self.scene)["ok"])
    def test_slow_pace(self):
        self.scene["performance"]["pace"] = "slow"; self.reject("pace")
    def test_depressed_affect(self):
        self.scene["performance"]["affect"] = "depressed"; self.reject("affect")
    def test_ground_gaze(self):
        self.scene["performance"]["gaze"] = "ground"; self.reject("gaze")
    def test_wine_semantics(self):
        self.scene["semantic_policy"]["residual_wine"] = "liquid_only"; self.reject("intoxication")
    def test_inference_semantics(self):
        self.scene["semantic_policy"]["inference"] = "verified"; self.reject("inference")
    def test_classical_dialogue(self):
        self.scene["dialogues"][0]["text"] = "知否，知否？"; self.reject("classical")
    def test_original_spoken(self):
        self.scene["dialogues"][0]["text"] = "昨夜雨疏风骤"; self.reject("verse used")
    def test_classical_voiceover(self):
        self.scene["voiceovers"][0]["text"] = "可曾知晓"; self.reject("classical")
    def test_unknown_source(self):
        self.scene["dialogues"][0]["source_ids"] = ["missing"]; self.reject("unknown reference")
    def test_empty_source_references(self):
        self.scene["dialogues"][0]["source_ids"] = []; self.reject("cannot be empty")
    def test_duplicate_id(self):
        self.scene["dialogues"].append(copy.deepcopy(self.scene["dialogues"][0])); self.reject("duplicate id")
    def test_unknown_speaker(self):
        self.scene["dialogues"][0]["speaker"] = "unknown"; self.reject("unknown speaker")
    def test_caption_changed(self):
        self.scene["poem_captions"][-1]["text"] = "绿肥红瘦"; self.reject("changed source")
    def test_poem_caption_not_speech(self):
        self.assertIn("应是绿肥红瘦", str(self.scene["poem_captions"]))
        self.assertTrue(module.validate(self.scene)["ok"])
    def test_dialogue_over_object(self):
        self.scene["shots"][0]["kind"] = "object"; self.reject("dialogue over")
    def test_speaker_hidden(self):
        self.scene["shots"][0]["visible_speakers"] = []; self.reject("speaker not visible")
    def test_voice_collision(self):
        self.scene["shots"][0]["voiceover_ids"] = ["N1"]; self.reject("narration overlap")
    def test_caption_collision(self):
        self.scene["shots"][0]["caption_ids"] = ["T1"]; self.reject("subtitle tracks")
    def test_bad_action(self):
        self.scene["shots"][0]["action"] = "缓缓挪步，垂眼叹气。"; self.reject("performance")
    def test_camera_slow_is_not_actor_slow(self):
        self.scene["shots"][0]["camera"] = "technical note: slow lens breathing compensation"
        self.assertTrue(module.validate(self.scene)["ok"])
    def test_long_insert_warns(self):
        self.scene["shots"][2]["duration_hint_s"] = 6
        result = module.validate(self.scene)
        self.assertTrue(result["ok"]); self.assertTrue(result["warnings"])
    def test_invalid_duration(self):
        self.scene["shots"][0]["duration_hint_s"] = True; self.reject("duration")
    def test_missing_manual_review(self):
        self.scene["manual_review_required"] = False; self.reject("manual review")
    def test_malformed_rows(self):
        self.scene["shots"].append("bad"); self.reject("needs an object")
    def test_missing_shots(self):
        self.scene["shots"] = None; self.reject("shots must")
    def test_reaction_insert_allowed_with_return(self):
        reaction = copy.deepcopy(self.scene["shots"][0])
        reaction.update(id="reaction", visible_speakers=["卷帘人"], reaction_insert=True, return_to="场-关系", duration_hint_s=1)
        self.scene["shots"].insert(1, reaction)
        self.assertTrue(module.validate(self.scene)["ok"])
    def test_reaction_cannot_open_dialogue(self):
        self.scene["shots"][0].update(reaction_insert=True, return_to="场-关系")
        self.reject("enter on speaker")
    def test_invalid_reaction_target(self):
        reaction = copy.deepcopy(self.scene["shots"][0])
        reaction.update(id="reaction", reaction_insert=True, return_to=[], duration_hint_s=1)
        self.scene["shots"].insert(1, reaction)
        self.reject("reaction needs")
    def test_plain_scene_does_not_require_poem_captions(self):
        self.scene["source_kind"] = "scene"
        self.scene["poem_captions"] = []
        for shot in self.scene["shots"]: shot["caption_ids"] = []
        self.assertTrue(module.validate(self.scene)["ok"])
    def test_invalid_source_kind(self):
        self.scene["source_kind"] = "anything"; self.reject("source_kind")
    def test_bad_json_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            f = Path(directory) / "bad.json"; f.write_text("{", encoding="utf-8")
            run = subprocess.run([sys.executable, str(ROOT / "scripts/validate_scene.py"), str(f)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2); self.assertFalse(json.loads(run.stdout)["ok"])
    def test_manifests_and_skill(self):
        for folder in (".claude-plugin", ".codex-plugin"):
            obj = json.loads((ROOT / folder / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(obj["name"], "dramascene"); self.assertEqual(obj["version"], "1.0.0")
            self.assertTrue((ROOT / obj["skills"]).is_dir())
        text = (ROOT / "skills/drama-scene-optimization/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: drama-scene-optimization\ndescription: "))
    def test_readable_case_contains_all_spoken_lines(self):
        text = (ROOT / "examples/lianwai/scene.md").read_text(encoding="utf-8")
        for row in BASE["dialogues"] + BASE["voiceovers"] + BASE["poem_captions"]:
            self.assertIn(row["text"], text)

if __name__ == "__main__": unittest.main()
