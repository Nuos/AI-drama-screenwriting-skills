"""New context/outdoor/narration/effect contract; no external service calls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator_v11', ROOT / 'scripts/validate_scene.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BASE = json.loads((ROOT / 'examples/lianwai/scene.json').read_text(encoding='utf-8'))

class ContractTests(unittest.TestCase):
    def setUp(self): self.s = copy.deepcopy(BASE)
    def reject(self, message):
        r = module.validate(self.s)
        self.assertFalse(r['ok'], r)
        self.assertTrue(any(message in e for e in r['errors']), r)
    def test_new_baseline(self):
        self.assertEqual(module.validate(self.s), {'ok': True, 'errors': [], 'warnings': [], 'manual_review_required': True})
    def test_version(self):
        self.assertEqual(self.s['case_version'], '3.0.0')
    def test_context_only_dialogue_allowed(self):
        self.assertEqual(self.s['dialogues'][0]['source_ids'], [])
        self.assertTrue(module.validate(self.s)['ok'])
    def test_missing_context(self):
        del self.s['context_facts']; self.reject('context_facts')
    def test_context_table_type(self):
        self.s['context_facts'] = {}; self.reject('context_facts')
    def test_context_row_type(self):
        self.s['context_facts'][0] = None; self.reject('rows need')
    def test_context_duplicate(self):
        self.s['context_facts'].append(copy.deepcopy(self.s['context_facts'][0])); self.reject('duplicate id')
    def test_fake_source_context(self):
        self.s['context_facts'][0]['origin'] = 'source_text'; self.reject('needs evidence')
    def test_unknown_context_origin(self):
        self.s['context_facts'][0]['origin'] = 'historical_guess'; self.reject('origin')
    def test_unknown_context_id(self):
        self.s['dialogues'][0]['context_ids'] = ['absent']; self.reject('context reference')
    def test_context_refs_type(self):
        self.s['dialogues'][0]['context_ids'] = None; self.reject('string array')
    def test_unanchored_speech(self):
        self.s['dialogues'][0]['context_ids'] = []; self.reject('source or context')
    def test_missing_order(self):
        del self.s['dialogue_order']; self.reject('dialogue_order')
    def test_duplicate_order(self):
        self.s['dialogue_order'].append('D1'); self.reject('duplicate')
    def test_broken_reply(self):
        self.s['dialogues'][4]['reply_to'] = 'D1'; self.reject('continuation')
    def test_first_reply(self):
        self.s['dialogues'][0]['reply_to'] = 'D10'; self.reject('continuation')
    def test_missing_speech_action(self):
        self.s['dialogues'][2]['speech_action'] = ''; self.reject('speech_action')
    def test_dialogue_reordered_in_shots(self):
        a,b=next(x for x in self.s['shots'] if x['id']=='人-D1'),next(x for x in self.s['shots'] if x['id']=='人-D3')
        a['dialogue_ids'],b['dialogue_ids']=b['dialogue_ids'],a['dialogue_ids'];self.reject('shot dialogue order')
    def test_setting_type(self):
        self.s['setting'] = None; self.reject('setting must')
    def test_missing_setting(self):
        del self.s['setting']; self.reject('setting')
    def test_invalid_setting_mode(self):
        self.s['setting']['mode']='mixed';self.reject('setting mode')
    def test_unjustified_override(self):
        self.s['setting']['mode']='user_override';self.reject('explicit user')
    def test_covered_location(self):
        self.s['setting']['locations'][0]['roof']='roofed';self.reject('open sky')
    def test_architecture_active(self):
        self.s['setting']['architecture_role']='main_room';self.reject('background prop')
    def test_unknown_location(self):
        self.s['shots'][0]['location_id']='elsewhere';self.reject('shot location')
    def test_location_unhashable(self):
        self.s['shots'][0]['location_id']=[];self.reject('shot location')
    def test_duplicate_location(self):
        self.s['setting']['locations'].append(copy.deepcopy(self.s['setting']['locations'][0]));self.reject('duplicate location')
    def test_indoor_actor(self):
        self.s['shots'][0]['environment']='indoor';self.reject('must be outdoor')
    def test_indoor_camera(self):
        self.s['shots'][0]['camera_environment']='indoor';self.reject('must be outdoor')
    def test_hidden_indoor_action(self):
        self.s['shots'][0]['action']='女子走进屋，拿起茶杯。';self.reject('indoor shot text')
    def test_hidden_indoor_camera(self):
        self.s['shots'][0]['camera']='摄影机从窗内向庭院拍。';self.reject('indoor shot text')
    def test_master_indoor(self):
        self.s['space']='室内看海棠';self.reject('indoor master')
    def test_narrator_analytical_function(self):
        self.s['voiceovers'][0]['function']='word_explanation';self.reject('add background')
    def test_narrator_mind_reading(self):
        self.s['voiceovers'][0]['text']='她心里想要留住花开的样子。';self.reject('mind-reading')
    def test_narrator_not_but(self):
        self.s['voiceovers'][0]['text']='她关心的不是花，而是青春。';self.reject('analytical')
    def test_narrator_not_also(self):
        self.s['voiceovers'][0]['text']='她不只看见花，还想到季节。';self.reject('analytical')
    def test_narrator_old_should(self):
        self.s['voiceovers'][0]['text']='这里的应该带着猜测。';self.reject('analytical')
    def test_narrator_repeats_dialogue(self):
        self.s['voiceovers'][0]['text']=self.s['dialogues'][0]['text'];self.reject('repeats dialogue')
    def test_narrator_missing_added_fact(self):
        self.s['voiceovers'][0]['added_context_ids']=[];self.reject('supported added information')
    def test_narrator_invalid_added_fact(self):
        self.s['voiceovers'][0]['added_context_ids']=['C4'];self.reject('supported added information')
    def test_narrator_no_new_information(self):
        self.s['voiceovers'][0].update(context_ids=['C4'],added_context_ids=['C4']);self.reject('no new context')
    def test_dialogue_ordinary_negative_allowed(self):
        self.s['dialogues'][0]['text']='茶不烫，杯子还在桌上。';self.assertTrue(module.validate(self.s)['ok'])
    def test_fictional_background_allowed(self):
        self.s['context_facts'][0]['text']='小园只在花香响起时开放。';self.assertTrue(module.validate(self.s)['ok'])
    def test_optional_narration(self):
        self.s['voiceovers']=[]
        for x in self.s['shots']:x['voiceover_ids']=[]
        self.assertTrue(module.validate(self.s)['ok'])
    def test_effect_permission(self):
        self.s['adaptation_policy']['allow_imagination']=False;self.reject('authorization')
    def test_effect_policy_type(self):
        self.s['adaptation_policy']=[];self.reject('adaptation_policy')
    def test_effect_empty_provenance(self):
        self.s['adaptation_policy']['note']='';self.reject('provenance note')
    def test_effect_replay(self):
        self.s['effects'][0]['time_mode']='past_replay';self.reject('reenact past')
    def test_effect_reality(self):
        self.s['effects'][0]['reality_layer']='historical_record';self.reject('expressive layer')
    def test_effect_music_missing(self):
        del self.s['effects'][0]['music'];self.reject('needs music')
    def test_effect_return_missing(self):
        del self.s['effects'][0]['return_rule'];self.reject('needs return_rule')
    def test_effect_bad_trigger(self):
        self.s['effects'][0]['trigger_dialogue_id']='D99';self.reject('trigger invalid')
    def test_unused_effect(self):
        for s in self.s['shots']:s['effect_ids']=[]
        self.reject('unused effect')
    def test_unknown_effect(self):
        self.s['shots'][0]['effect_ids']=['E99'];self.reject('unknown effect')
    def test_effect_at_wrong_dialogue(self):
        self.s['effects'][0]['trigger_dialogue_id']='D1';self.reject('trigger shot')
    def test_no_effects_allowed(self):
        self.s['effects']=[];self.s['adaptation_policy']['allow_imagination']=False
        for s in self.s['shots']:s['effect_ids']=[]
        self.assertTrue(module.validate(self.s)['ok'])
    def test_malformed_structure_no_crash(self):
        self.s['structure']=[];self.reject('structure')
    def test_malformed_trigger_shot_no_crash(self):
        next(x for x in self.s['shots'] if x['effect_ids'])['dialogue_ids']=None;self.reject('string array')
    def test_all_spoken_and_caption_text_in_readable(self):
        text=(ROOT/'examples/lianwai/scene.md').read_text(encoding='utf-8')
        for x in BASE['dialogues']+BASE['voiceovers']+BASE['poem_captions']:self.assertIn(x['text'],text)
    def test_all_shots_in_readable(self):
        text=(ROOT/'examples/lianwai/scene.md').read_text(encoding='utf-8')
        for x in BASE['shots']:self.assertIn(x['id'],text)

if __name__ == '__main__': unittest.main()
