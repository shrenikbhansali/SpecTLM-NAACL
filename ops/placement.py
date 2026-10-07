"""Site-only launcher placement. Evaluation settings are untouched."""
import os


def launcher_placement(args):
    args=list(args);head=args[:args.index('--')] if '--' in args else args
    ice=os.environ.get('SITE')=='ice'
    if '--node' in head or '--gpus' in head:
        if '--node' not in head or '--gpus' not in head:raise ValueError('incomplete launcher placement')
        if ice and (head[head.index('--node')+1],head[head.index('--gpus')+1])!=('slurm','slurm'):raise ValueError('ICE requires Slurm placement')
        return args
    return ['--node','slurm' if ice else 'heck-srv4','--gpus','slurm' if ice else '0',*args]


def place_job(job,heck_nodes=None):
    result=dict(job)
    if os.environ.get('SITE')=='ice':
        result['allowed_nodes']=['slurm'];result['args']=launcher_placement(job['args'])
    elif heck_nodes is not None:result['allowed_nodes']=list(heck_nodes)
    return result
