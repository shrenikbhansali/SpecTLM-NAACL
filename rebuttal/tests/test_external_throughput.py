import unittest
from followspec.family_repair import supervision_source


class ExternalThroughputTests(unittest.TestCase):
    def test_default_rejects_foreign_responses(self):
        with self.assertRaises(ValueError):supervision_source({'id':'target','revision':'rev','path':'/p'},[{'generation_target':'foreign','generation_revision':None}],None)

    def test_explicit_pinned_native_data_keeps_actual_teacher(self):
        target={'id':'target','revision':'rev','path':'/p'}
        manifest={'mode':'E3a-native-throughput','dataset_id':'open-thoughts/OpenThoughts-114k','dataset_revision':'a'*40,'response_model':'deepseek-ai/DeepSeek-R1','response_model_revision':None}
        rows=[{'generation_target':manifest['response_model'],'generation_revision':None,'response_dataset':manifest['dataset_id'],'response_dataset_revision':manifest['dataset_revision']}]
        self.assertEqual(supervision_source(target,rows,None,manifest),target)
        self.assertEqual(rows[0]['generation_target'],'deepseek-ai/DeepSeek-R1')
        rows[0]['response_dataset_revision']='other'
        with self.assertRaises(ValueError):supervision_source(target,rows,None,manifest)

    def test_native_mode_requires_pinned_provenance(self):
        with self.assertRaises(ValueError):supervision_source({'id':'a','path':'p','revision':'r'},[],None,{'mode':'E3a-native-throughput'})
