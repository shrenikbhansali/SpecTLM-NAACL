"""Opt-in synchronized whole-step timing, with export intervals excluded."""
class StepProfiler:
    def __init__(self,clock,synchronize,memory):
        self.clock=clock;self.synchronize=synchronize;self.memory=memory
    def begin(self):
        self.synchronize();self.started=self.clock()
    def end(self,step):
        self.synchronize();elapsed=self.clock()-self.started;allocated,reserved=self.memory()
        return dict(step=step,wall_s=elapsed,peak_allocated_bytes=allocated,peak_reserved_bytes=reserved,scope='data/target capture plus drafter forward/backward/optimizer; exports excluded')
