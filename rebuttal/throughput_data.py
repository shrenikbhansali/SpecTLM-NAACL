"""E3a-only measured-throughput inputs; no changes to repair recipes or defaults."""
import argparse
import hashlib
import json
from pathlib import Path


def mixture_counts(n):
    share = round(n * 68 / 532)
    return share, n - share


def clip_response(row, maximum=2049):
    prompt = row['prompt_token_ids']
    if len(prompt) >= maximum:
        raise ValueError('Cannot retain the whole prompt and an answer token')
    answer = row['completion_token_ids'][:maximum-len(prompt)]
    if not answer:
        raise ValueError('Empty answer')
    result = row | dict(input_ids=prompt+answer, completion_token_ids=answer,
                        response_start=len(prompt), loss_mask=[False]*len(prompt)+[True]*len(answer))
    return result, dict(original_tokens=len(row['input_ids']), kept_tokens=len(result['input_ids']),
                        removed_answer_tokens=len(row['completion_token_ids'])-len(answer))


def main():
    import pyarrow.parquet as pq
    from followspec.independent_kd import read, write, jsonl, filter_training_queries
    from followspec.repair_data import tokenizer_for, render
    from atlas.workloads import file_hash
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); root = a.workspace
    a.output.mkdir(parents=True, exist_ok=False)
    ultra = json.loads((a.sources/'ultrachat-complete.json').read_text())
    share = json.loads((root/'rebuttal/E45_sources_20261124/dataset-complete.json').read_text())
    target = json.loads((root/'rebuttal/inputs/target-0.json').read_text())
    tok = tokenizer_for(target['path'])
    key = lambda text: hashlib.sha256(('E3a-seed0\0'+text).encode()).hexdigest()
    pools = {'sharegpt': [], 'ultrachat': []}
    for r in json.loads((Path(share['path'])/'ShareGPT_V3_unfiltered_cleaned_split.json').read_text()):
        turns = r.get('conversations', [])
        if turns and turns[0].get('from') in ['human', 'user']:
            text = turns[0]['value']
            if text.strip():
                pools['sharegpt'].append(dict(prompt=text, prompt_id='E3a-sharegpt-'+key(text), source='sharegpt'))
    for f in sorted((Path(ultra['path'])/'data').glob('train_*.parquet')):
        for batch in pq.ParquetFile(f).iter_batches(columns=['prompt', 'prompt_id'], batch_size=2048):
            for r in batch.to_pylist():
                if r['prompt'].strip():
                    pools['ultrachat'].append(dict(prompt=r['prompt'], prompt_id='E3a-ultrachat-'+r['prompt_id'], source='ultrachat'))
    counts = {k: len(v) for k, v in pools.items()}
    candidates = []
    for name, pool in pools.items():
        for r in sorted(pool, key=lambda r:key(r['prompt'])):
            # Same 2000 prompts for both caps. Whole prompts, no silent truncation.
            if len(render(tok, r['prompt'])) <= 1536:
                candidates.append(r)
            if sum(x['source'] == name for x in candidates) >= 4000:
                break
    forbidden = root/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl'
    filtered, report = filter_training_queries(candidates, [r.get('raw_prompt', r.get('prompt')) for r in read(forbidden)])
    quotas = dict(zip(['sharegpt','ultrachat'], mixture_counts(2000)))
    selected = []
    for name, n in quotas.items():
        subset = [r for r in filtered if r['source'] == name][:n]
        if len(subset) != n:
            raise ValueError('Deduplicated mixture shortfall')
        selected.extend(subset)
    selected.sort(key=lambda r:key(r['prompt']))
    jsonl(a.output/'queries.jsonl', selected)
    write(a.output/'manifest.json', dict(n=2000, quotas=quotas, available_source_counts=counts,
          sources={k:{z:v[z] for z in ['repo','revision','license']} for k,v in [('sharegpt',share),('ultrachat',ultra)]},
          query_sha256=file_hash(a.output/'queries.jsonl'), forbidden_sha256=file_hash(forbidden),
          deduplication=report, selection='fixed seed0 hash ordering; first user instruction; max1536 rendered prompt tokens; no source answers',
          response_caps=[512,2048], training_context_budget=4096))
    write(a.output/'five_rendered_queries.json', [r|dict(decoded=tok.decode(render(tok,r['prompt'])),
          rendered_token_ids=render(tok,r['prompt'])) for r in selected[:5]])


if __name__ == '__main__':
    main()
