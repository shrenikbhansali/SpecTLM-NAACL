"""Opt-in subdivision of native batches; preserves every selected token/sample.

Production adoption is a research decision. The native sampler stays unchanged.
"""
POLICY = 'native_split_max_v1'


def subdivide_batches(batches, lengths, target_steps, capacity):
    batches = [[int(i) for i in b] for b in batches]
    flat = [i for b in batches for i in b]
    if (not batches or any(not b for b in batches) or sorted(flat) != list(range(len(lengths)))
            or any(type(n) is not int or not 0 < n <= capacity for n in lengths)
            or any(sum(lengths[i] for i in b) > capacity for b in batches)):
        raise ValueError('invalid native batches, coverage or capacity')
    if type(target_steps) is not int or not len(batches) <= target_steps <= len(lengths):
        raise ValueError('cannot reach requested steps by nonempty subdivision')
    events = []
    while len(batches) < target_steps:
        # Largest eligible token load, then earliest current batch.
        index = max((j for j,b in enumerate(batches) if len(b)>1),
                    key=lambda j:(sum(lengths[i] for i in batches[j]),-j))
        original = batches[index];total = sum(lengths[i] for i in original)
        prefix = 0;cuts = []
        for cut,i in enumerate(original[:-1],1):
            prefix += lengths[i];cuts.append((abs(total-2*prefix),cut))
        cut = min(cuts)[1];left,right = original[:cut],original[cut:]
        events.append(dict(batch_index=index,original=original,left=left,right=right,
                           original_tokens=total,left_tokens=sum(lengths[i] for i in left)))
        batches[index:index+1] = [left,right]
    return batches,events


class StepMatchedSampler:
    def __init__(self, *, factory, target_steps, **kwargs):
        if kwargs['num_replicas'] != 1 or kwargs['rank'] != 0:
            raise ValueError('step subdivision requires one replica')
        self.native = factory(**kwargs);self.target_steps = target_steps
        self.lengths = kwargs['lengths'];self.capacity = kwargs['batch_max_length']
        self.epoch = 0;self._cache = None

    def set_epoch(self, epoch):
        self.native.set_epoch(epoch);self.epoch = epoch;self._cache = None

    def _batches(self):
        if self._cache is None:
            self._cache,self.events = subdivide_batches(list(self.native),self.lengths,self.target_steps,self.capacity)
        return self._cache

    def __iter__(self):return iter(self._batches())
    def __len__(self):return len(self._batches())


def inspect_matched_batches(lengths, *, factory, batch_max_length, seeds, epochs, replicas):
    from followspec.audit_batches import inspect_batches
    if epochs != 1 or replicas != 1:
        raise ValueError('step subdivision currently requires one epoch and one replica')
    native = {};counts = {}
    for seed in seeds:
        for arm,values in lengths.items():
            sampler = factory(batch_max_length=batch_max_length,lengths=values,num_replicas=1,rank=0,seed=seed)
            sampler.set_epoch(0);batches = [[int(i) for i in b] for b in sampler]
            native[arm,seed] = batches;counts[f'{arm}:{seed}'] = len(batches)
    target = max(counts.values());events = []
    for (arm,seed),batches in native.items():
        _,splits = subdivide_batches(batches,lengths[arm],target,batch_max_length)
        events.extend(dict(arm=arm,seed=seed,epoch=0,**event) for event in splits)
    def matched(**kwargs):return StepMatchedSampler(factory=factory,target_steps=target,**kwargs)
    report = inspect_batches(lengths,factory=matched,batch_max_length=batch_max_length,seeds=seeds,epochs=epochs,replicas=replicas)
    return report|dict(batch_step_policy=POLICY,native_step_counts=counts,subdivision_events=events)
