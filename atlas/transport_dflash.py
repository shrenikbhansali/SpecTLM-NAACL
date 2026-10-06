"""Native DFlash blocks with independently crossed base/child output heads."""
import torch


def load_dflash(path,base):
    from speculators.version import git_commit
    from speculators.convert.dflash.converter import DFlashConverter,_VERIFIER_FILLED_KEYS
    from speculators.convert.utils import load_checkpoint_config,load_checkpoint_weights
    from speculators.models.dflash import DFlashDraftModel
    if git_commit!='261a82dd44ca05ff73006938c0614111bb2dd2b7':raise ValueError('wrong pinned native backend')
    source=load_checkpoint_config(path);body=load_checkpoint_weights(path)
    converter=DFlashConverter();cfg=converter._build_config(source,base,None)
    cfg.transformer_layer_config._attn_implementation='eager'
    model=DFlashDraftModel(cfg)
    # This released checkpoint already uses the native body tensor names. No
    # remapping, slicing, random replacement or on-disk weight conversion.
    missing,unexpected=model.load_state_dict(body,strict=False,assign=True)
    if unexpected or set(missing)-_VERIFIER_FILLED_KEYS:raise ValueError('external DFlash body does not exactly match native model')
    model.load_verifier_weights();model=model.to(dtype=torch.bfloat16).eval()
    for name,tensor in body.items():
        if not torch.equal(model.state_dict()[name],tensor):raise ValueError('DFlash conversion changed body weights')
    return model.to('cuda')


def capture_dflash_hidden(model,features,input_ids,last_hidden,response_start):
    if model.training or model.config.sample_from_anchor:raise ValueError('eval DFlash with bonus-token anchor required')
    if input_ids.ndim!=2 or input_ids.shape[0]!=1 or features.shape[:2]!=input_ids.shape or last_hidden.shape[:2]!=input_ids.shape:
        raise ValueError('one aligned DFlash feature/token sequence required')
    length=input_ids.shape[1];block=model.block_size
    if type(response_start) is not int or not 1<=response_start<length-block:raise ValueError('no complete native answer blocks')
    mask=torch.zeros_like(input_ids,dtype=torch.bool);mask[:,response_start:]=True
    expected=torch.arange(response_start,length-block,device=input_ids.device)
    with torch.inference_mode():
        hidden,_,_,scored,indices=model._backbone_forward(hidden_states=features,input_ids=input_ids,
            loss_mask=mask,verifier_last_hidden_states=last_hidden,document_ids=torch.zeros_like(input_ids),max_anchors=len(expected))
    # Selecting every eligible anchor makes the native random permutation an
    # exact deterministic set. Keep its conservative full-block end boundary.
    indices=indices.reshape(-1,block);scored=scored.reshape(-1,block)
    if not torch.equal(indices[:,0],expected) or not torch.equal(indices,expected[:,None]+torch.arange(block,device=indices.device)):
        raise ValueError('native DFlash anchor ordering/alignment changed')
    if scored[:,0].any() or not scored[:,1:].all():raise ValueError('native DFlash mask must exclude only the anchor slot')
    hidden=hidden[0].reshape(len(expected),block,-1).detach().cpu()
    if not torch.isfinite(hidden).all():raise ValueError('nonfinite DFlash hidden states')
    return dict(hidden=hidden,anchors=expected.cpu(),block_size=block,sequence_length=length)


def align_dflash_step(target_logits,captured,step):
    block=captured['block_size'];anchors=captured['anchors'];hidden=captured['hidden']
    if type(step) is not int or not 0<=step<block-1:raise ValueError('DFlash position must follow bonus anchor')
    if target_logits.ndim!=2 or len(target_logits)!=captured['sequence_length'] or hidden.shape[:2]!=(len(anchors),block):
        raise ValueError('DFlash target/hidden shape mismatch')
    return target_logits[(anchors+step).to(target_logits.device)],hidden[:,step+1],anchors


def project_head(head,hidden):
    device=next(head.parameters()).device
    with torch.inference_mode():
        return torch.cat([head(chunk.to(device)).float().cpu() for chunk in hidden.split(64)])
