"""Independent tensor-level proof that an EDA export retains every frozen weight."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from safetensors import safe_open


def mapping(folder):
    folder = Path(folder)
    index = folder / 'model.safetensors.index.json'
    if index.exists():
        return {k: folder / v for k, v in json.loads(index.read_text())['weight_map'].items()}
    with safe_open(str(folder / 'model.safetensors'), framework='pt', device='cpu') as f:
        return {k: folder / 'model.safetensors' for k in f.keys()}


def load(paths, name):
    with safe_open(str(paths[name]), framework='pt', device='cpu') as f:
        return f.get_tensor(name)


def digest(tensor):
    return hashlib.sha256(tensor.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


def frozen_part(name, original, exported):
    if name.startswith('layers.0.mlp.'):
        if 'down_proj' in name:
            part = exported[:, :original.shape[1]]
        else:
            part = exported[:original.shape[0]]
    else:
        part = exported
    if part.shape != original.shape:
        raise ValueError('changed frozen shape: ' + name)
    return part


def verify(initial, export, target):
    old, new, teacher = map(mapping, [initial, export, target])
    if set(new) != set(old) | {'embed_tokens.weight'}:
        raise ValueError('unexpected export keys')
    evidence = []
    for name in sorted(new):
        original = load(teacher, 'model.embed_tokens.weight') if name == 'embed_tokens.weight' else load(old, name)
        actual = frozen_part(name, original, load(new, name))
        expected = original.to(actual.dtype)
        if not torch.equal(expected, actual):
            raise ValueError('frozen weight changed: ' + name)
        evidence.append(dict(name=name, sha256=digest(actual), shape=list(actual.shape),
                             dtype=str(actual.dtype), exact=True))
    return dict(passed=True, initial=str(initial), export=str(export), target=str(target),
                scope='every frozen tensor; shared MLP prefix and FIX24 target embedding included', tensors=evidence)


def main():
    from rebuttal.dispatch_exports import write_immutable
    p = argparse.ArgumentParser()
    for name in ['initial', 'export', 'target', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    result = verify(a.initial, a.export, a.target)
    write_immutable(a.output, result)
    print(json.dumps({'passed': result['passed'], 'tensors': len(result['tensors'])}))


if __name__ == '__main__':
    main()
