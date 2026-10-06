"""One frozen base and at most one resident bank adapter for online batches.

Registry entries come from B5's audited, pinned bank manifest. Mixtures are
intentionally not admitted until B3's numerical acceptance is resolved.
"""
from pathlib import Path
import threading
from atlas.run_cell import sha256
from atlas.generate_magpie import unpaused
from followspec.online_capture import OnlinePairCapture


def load_adapter(base,path):
    from peft import PeftModel
    return PeftModel.from_pretrained(base,path,autocast_adapter_dtype=False).eval().requires_grad_(False)


class FrozenAdapterBank:
    def __init__(self,base,registry,taps,draft_tokens,*,pause_check=unpaused,loader=load_adapter,capture_factory=OnlinePairCapture):
        if 'base' in registry or any(r.get('kind')!='bank' for r in registry.values()):
            raise ValueError('registry must contain only audited bank adapters; no mixture or heldout target')
        for r in registry.values():
            if not r.get('revision') or not r.get('path') or not r.get('files_sha256'):raise ValueError('pinned adapter files required')
            if any(Path(name).is_absolute() or '..' in Path(name).parts for name in r['files_sha256']):raise ValueError('invalid adapter file path')
        self.base=base.eval().requires_grad_(False);self.model=self.base;self.registry=registry
        self.current=None;self.broken=False;self.taps=taps;self.tokens=draft_tokens;self.pause_check=pause_check
        self.loader=loader;self.factory=capture_factory;self.lock=threading.Lock()
        self.provider=self.factory(self.model,taps,draft_tokens,pause_check=pause_check)

    @property
    def resident_adapters(self):return int(self.current is not None)

    def _select(self,target):
        self.pause_check()
        if target=='base':return 'base'
        if target not in self.registry:raise ValueError('target absent from audited bank')
        if target==self.current:return 'child'
        item=self.registry[target]
        # Hash before unloading the current adapter; a bad next target leaves
        # the current valid state untouched. No full feature/adapter bank cache.
        for name,digest in item['files_sha256'].items():
            if sha256(Path(item['path'])/name)!=digest:raise ValueError('adapter file hash mismatch')
        self.provider=None
        if self.current is not None:
            self.model=self.model.unload()
            if self.model is not self.base:raise ValueError('PEFT unload replaced the base instance')
            self.current=None
        try:
            self.model=self.loader(self.base,item['path'])
            self.current=target
            self.provider=self.factory(self.model,self.taps,self.tokens,pause_check=self.pause_check)
        except Exception:
            # Loading failures are fatal to this training step. Never return a
            # previous adapter's features as if they belonged to the new child.
            self.provider=None;self.broken=True
            raise
        return 'child'

    def capture(self,target,input_ids,loss_mask,*,feature_target=None):
        with self.lock:
            if self.broken:raise RuntimeError('target loader is unusable after a failed load')
            if target=='base' and feature_target=='child':raise ValueError('base records cannot request resident child features')
            route=self._select(target)
            if feature_target not in {None,'base','child'}:raise ValueError('invalid feature route')
            if self.provider is None:raise RuntimeError('target loader is unusable after a failed load')
            return self.provider(input_ids,loss_mask,feature_target=feature_target or route)
