from types import SimpleNamespace
from atlas.timing_panel import timed_passes


def test_cold_warm_use_identical_ids_and_keep_batch_times_once():
    seen=[]
    class Engine:
        def generate(self,rows,sampling,use_tqdm):
            seen.append(rows)
            return [SimpleNamespace(prompt_token_ids=r['prompt_token_ids'],outputs=[SimpleNamespace(token_ids=[3,4])]) for r in rows]
    rows=[dict(prompt_id=str(i),rendered_token_ids=[i+1]) for i in range(3)]
    counter=iter(range(100));out=timed_passes(Engine(),None,rows,2,2,lambda:None,lambda:next(counter))
    assert [x['phase'] for x in out]==['cold','warm','warm']
    assert all(x['generation_wall_s']==2 and x['n']==3 and x['output_tokens']==6 for x in out)
    assert seen[:2]==seen[2:4]==seen[4:6]
    assert all(x['matches_first_pass'] for x in out)
