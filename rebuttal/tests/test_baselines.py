import unittest
from rebuttal.baselines import raw_metric, paired, validate_config


class BaselineTests(unittest.TestCase):
    def test_tau_includes_bonus_and_position_one(self):
        self.assertEqual(raw_metric({'per_step_accepted':[0,2,4],'per_step_drafted':[4,4,4]}),(3.,2/3))
        self.assertIsNone(raw_metric({'per_step_accepted':[],'per_step_drafted':[]}))
        with self.assertRaises(ValueError):raw_metric({'per_step_accepted':[5],'per_step_drafted':[4]})

    def test_pairwise_zero_steps_and_identity(self):
        a=[dict(prompt_id='a',per_step_accepted=[0,2],per_step_drafted=[4,4]),dict(prompt_id='b',per_step_accepted=[],per_step_drafted=[])]
        b=[dict(prompt_id='a',per_step_accepted=[1,3],per_step_drafted=[4,4]),dict(prompt_id='b',per_step_accepted=[1],per_step_drafted=[4])]
        got=paired(a,b)
        self.assertEqual(got['n'],1);self.assertEqual(got['excluded_zero_step'],1)
        self.assertEqual(got['delta_tau'],1.);self.assertEqual(got['delta_tau_ci95'],[1.,1.])
        with self.assertRaises(ValueError):paired(a,b[:1])

    def test_exact_reproduction_rejects_converted_drafter(self):
        a = dict(prompt_sha256='p', K=4, seed=0, max_new_tokens=512,
                 batch_size=8, engine_version='0.31.0', target_revision='r',
                 drafter_revision='d', target_files_sha256={'weights':'t'},
                 drafter_files_sha256={'pytorch_model.bin':'released'},
                 code_commit='6da2e4265c0398ec0de5affaf23b0bd1df0be445')
        validate_config(a, dict(a))
        b = dict(a, drafter_files_sha256={'model.safetensors':'converted'})
        with self.assertRaises(ValueError):validate_config(a,b)
        b = dict(a, target_files_sha256={'weights':'t','README.md':'card','LICENSE':'license'})
        validate_config(a,b)
        b['target_files_sha256']['weights']='changed'
        with self.assertRaises(ValueError):validate_config(a,b)


if __name__=='__main__':unittest.main()
