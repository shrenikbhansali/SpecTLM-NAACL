import copy
import unittest
from rebuttal.timing_divergence import first_difference, matching_queries, restrict_complete_batches, pair_summary


def process(batch=1):
    rows=[{'prompt_id':str(i),'completion_token_ids':[1,2,3]} for i in range(4)]
    batches=[{'prompt_ids':[str(i) for i in range(j,j+batch)],'wall_s':float(batch)} for j in range(0,4,batch)]
    return {'config':{'prompt_sha256':'same','target_revision':'target','batch_size':batch,'max_new_tokens':512,'seed':0,'temperature':0,'max_model_len':4096,'gpu_memory_utilization':.7},
            'timing':{'startup_s':1,'passes':[{'per_prompt':copy.deepcopy(rows),'batches':copy.deepcopy(batches)} for _ in range(4)]}}


class TimingDivergenceTests(unittest.TestCase):
    def test_token_and_length_differences(self):
        self.assertIsNone(first_difference([1,2],[1,2]))
        self.assertEqual(first_difference([0,2],[1,2]),0)
        self.assertEqual(first_difference([1,2],[1,2,3]),2)
        self.assertEqual(first_difference([],[1]),0)

    def test_all_process_all_warm_intersection(self):
        cells=[process() for _ in range(6)]
        cells[-1]['timing']['passes'][3]['per_prompt'][0]['completion_token_ids']=[2]
        # Cold differences do not select the warm-output diagnostic subset.
        cells[0]['timing']['passes'][0]['per_prompt'][1]['completion_token_ids']=[4]
        self.assertEqual(matching_queries(cells),{'1','2','3'})

    def test_only_complete_timed_batches(self):
        cell=process(2)
        result,n=restrict_complete_batches([cell],{'0','2','3'})
        self.assertEqual(n,1)
        self.assertEqual(result[0]['timing']['passes'][1]['batches'][0]['prompt_ids'],['2','3'])
        self.assertEqual(result[0]['timing']['passes'][1]['batches'][0]['wall_s'],2)
        self.assertEqual(len(cell['timing']['passes'][1]['batches']),2)
        self.assertEqual(restrict_complete_batches([cell],{'0','2'})[1],0)

    def test_pair_summary_and_unpaired_inputs(self):
        a,b=process(),process()
        for p in b['timing']['passes'][1:]:p['per_prompt'][0]['completion_token_ids']=[1,5]
        s=pair_summary(a,b)
        self.assertEqual(s['identical_fraction'],.75)
        self.assertEqual(s['first_divergence_quartiles'],[1,1,1])
        b['config']['prompt_sha256']='different'
        with self.assertRaises(ValueError):pair_summary(a,b)
