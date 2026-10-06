"""Deterministic, source-traceable publication exhibits from explicit aggregates."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.cbook import boxplot_stats
import numpy as np

CATALOG={
 'method_figure1':dict(kind='points',description='Frozen and FS retention per held-out derivative'),
 'atlas_figure1':dict(kind='distribution',description='Retention by derivative type and drafter'),
 'method_figure2':dict(kind='line',description='Atlas retention and depth, use panel column for metrics'),
 'atlas_figure2':dict(kind='points',description='A10 against A00 by derivative'),
 'method_figure3':dict(kind='points',description='Per-derivative FS gains over each control'),
 'atlas_figure3':dict(kind='line',description='Relative loss over K, observed and Proposition1'),
 'method_figure4':dict(kind='points',transport=True,description='Diagnostic transport before and after FS'),
 'atlas_figure4':dict(kind='distribution',transport=True,description='Diagnostic transport ratio by type'),
 'method_table1':dict(kind='table',description='Arms and intended factors'),
 'atlas_table1':dict(kind='table',description='Pool composition by type'),
 'method_table2':dict(kind='table',description='Main results by arm and parent retention'),
 'atlas_table2':dict(kind='table',description='Prespecified cross-validated predictor results'),
 'appendix_ablations':dict(kind='points',description='Prespecified ablations'),
 'appendix_generality':dict(kind='table',description='DFlash and Qwen3 results'),
 'appendix_eagle31':dict(kind='table',description='EAGLE3.1 results'),
 'appendix_speedups':dict(kind='points',description='Dedicated-H200 timing results'),
 'appendix_derivatives':dict(kind='table',description='Full per-derivative cells'),
 'appendix_ledger_children':dict(kind='points',description='Remeasured ledger children'),
}


def numeric(value):
    try:x=float(value)
    except (ValueError,TypeError):return None
    if not math.isfinite(x):raise ValueError('nonfinite plot/table value')
    return x


def run_ids(row):
    values=json.loads(row['run_ids']) if row.get('run_ids') else [row.get('run_id')]
    if not isinstance(values,list) or not values or any(not isinstance(s,str) or not s.strip() for s in values):
        raise ValueError('each row needs nonempty source run IDs')
    return sorted(set(values))


def tex_escape(value):
    replacements={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(replacements.get(c,c) for c in str(value))


def macro_name(exhibit,row,column):
    digest=hashlib.sha256(f'{exhibit}:{row}:{column}'.encode()).hexdigest()[:16]
    return 'Exhibit'+digest.translate(str.maketrans('0123456789abcdef','abcdefghijklmnop'))


def render(spec,output):
    ident=spec['id']
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]*',ident):raise ValueError('invalid exhibit ID')
    spec=CATALOG.get(ident,{})|spec
    kind=spec['kind'];source=Path(spec['source'])
    if kind not in ('points','line','distribution','table'):raise ValueError('unsupported exhibit kind')
    with source.open(newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    if not rows:raise ValueError('empty aggregate')
    provenance=[dict(source_row=i+2,values=r,run_ids=run_ids(r)) for i,r in enumerate(rows)]
    if spec.get('transport') and any(r.get('diagnostic','').lower()!='true' for r in rows):
        raise ValueError('transport/hybrid rows must be explicitly diagnostic')
    engines={r['engine_version'] for r in rows if r.get('engine_version')}
    if engines and engines!={'0.31.0'}:raise ValueError('mixed/unpinned engine in exhibit')
    if 'synthetic' not in spec:raise ValueError('explicit synthetic=true/false required')
    title=spec.get('title',ident.replace('_',' '))
    if spec['synthetic']:title='SYNTHETIC ACCEPTANCE ONLY — '+title
    if spec.get('transport'):title='Diagnostic — '+title
    rc={'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'ps.fonttype':42,
        'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':100,'savefig.dpi':160}
    details=[];macros=[];table_text=None
    with matplotlib.rc_context(rc):
        if kind=='table':
            columns=spec['columns']
            if not columns or any(c not in fields for c in columns):raise ValueError('invalid table columns')
            display=[];tex_rows=[]
            for i,row in enumerate(rows):
                shown=[];tex=[]
                for column in columns:
                    value=numeric(row[column]);shown.append(format(value,'.6g') if value is not None else row[column])
                    if value is None:tex.append(tex_escape(row[column]))
                    else:
                        name=macro_name(ident,i,column);formatted=format(value,'.6g');tex.append('\\'+name)
                        macros.append(dict(name=name,value=value,formatted=formatted,column=column,source_row=i+2,run_ids=provenance[i]['run_ids']))
                display.append(shown);tex_rows.append(' & '.join(tex)+r' \\')
            table_text='\\begin{tabular}{'+'l'*len(columns)+'}\n'+' & '.join(map(tex_escape,columns))+r' \\'+'\n\\hline\n'+'\n'.join(tex_rows)+'\n\\end{tabular}\n'
            fig,ax=plt.subplots(figsize=(max(6.,len(columns)*1.25),max(2.,len(rows)*.25+1)))
            ax.axis('off');table=ax.table(cellText=display,colLabels=columns,loc='center');table.auto_set_font_size(False);table.set_fontsize(8);table.scale(1,1.3)
            ax.set_title(title,fontsize=10)
        else:
            xcol=spec['x'];ycol=spec['y'];series=spec.get('series');panel=spec.get('panel')
            for row in rows:
                if numeric(row[ycol]) is None:raise ValueError('y must be numeric')
                numeric(row[xcol])
                if bool(spec.get('low'))!=bool(spec.get('high')):raise ValueError('need both interval endpoints')
                if spec.get('low') and not float(row[spec['low']])<=float(row[ycol])<=float(row[spec['high']]):raise ValueError('invalid interval')
            panels=sorted({r[panel] for r in rows}) if panel else ['']
            fig,axes=plt.subplots(1,len(panels),figsize=(6.4*len(panels),3.6),squeeze=False)
            for ax,panel_value in zip(axes[0],panels):
                selected=[(i,r) for i,r in enumerate(rows) if not panel or r[panel]==panel_value]
                if kind=='distribution':
                    groups={}
                    for i,r in selected:
                        label=r[xcol]+(' / '+r[series] if series else '')
                        groups.setdefault(label,[]).append((i,r))
                    boxes=[]
                    for label,group in sorted(groups.items()):
                        values=[float(r[ycol]) for _,r in group];stat=boxplot_stats(values,whis=1.5)[0];stat['label']=label;boxes.append(stat)
                        details.append(dict(panel=panel_value,label=label,n=len(values),median=float(stat['med']),q1=float(stat['q1']),q3=float(stat['q3']),
                            whisker_low=float(stat['whislo']),whisker_high=float(stat['whishi']),fliers=stat['fliers'].tolist(),
                            source_rows=[i+2 for i,_ in group],run_ids=sorted({v for i,_ in group for v in provenance[i]['run_ids']})))
                    ax.bxp(boxes,showfliers=True);ax.tick_params(axis='x',rotation=35)
                else:
                    labels=list(dict.fromkeys(r[xcol] for _,r in selected));is_numeric=all(numeric(s) is not None for s in labels)
                    groups=sorted({r[series] for _,r in selected}) if series else ['']
                    for label in groups:
                        group=[(i,r) for i,r in selected if not series or r[series]==label]
                        group.sort(key=lambda item:float(item[1][xcol]) if is_numeric else labels.index(item[1][xcol]))
                        x=[float(r[xcol]) if is_numeric else labels.index(r[xcol]) for _,r in group];y=[float(r[ycol]) for _,r in group]
                        err=None
                        if spec.get('low'):err=np.array([[float(r[ycol])-float(r[spec['low']]),float(r[spec['high']])-float(r[ycol])] for _,r in group]).T
                        ax.errorbar(x,y,yerr=err,fmt='o-' if kind=='line' else 'o',markersize=3,capsize=2,label=label)
                    if not is_numeric:ax.set_xticks(range(len(labels)),labels,rotation=45,ha='right')
                    if series:ax.legend(frameon=False)
                ax.set_xlabel(spec.get('xlabel',xcol));ax.set_ylabel(spec.get('ylabel',ycol));ax.set_title(panel_value or title,fontsize=10)
                ax.grid(axis='y',alpha=.2)
            if panel:fig.suptitle(title,fontsize=10)
        fig.tight_layout()
        out=Path(output);out.mkdir(parents=True,exist_ok=False)
        fig.savefig(out/f'{ident}.pdf',metadata={'Creator':'SpecTLM deterministic exhibits','CreationDate':None,'ModDate':None})
        fig.savefig(out/f'{ident}.png',metadata={'Software':'SpecTLM deterministic exhibits'})
        plt.close(fig)
    if table_text is not None:
        (out/f'{ident}.tex').write_text(table_text)
        (out/f'{ident}.numbers.tex').write_text(''.join('\\newcommand{\\'+m['name']+'}{'+m['formatted']+'}\n' for m in macros))
    with (out/f'{ident}.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    sidecar=dict(spec=spec,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        source_run_ids=sorted({v for p in provenance for v in p['run_ids']}),data_rows=provenance,
        derived_marks=details,table_macros=macros,n_rows=len(rows),matplotlib_version=matplotlib.__version__,
        numpy_version=np.__version__,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        display_precision='6 significant digits; full source values retained',
        interpretation='explicit supplied aggregates only; no framing choice, predictor fitting, or gate decision')
    (out/f'{ident}.json').write_text(json.dumps(sidecar,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return sidecar


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest');p.add_argument('--output');p.add_argument('--catalog',action='store_true');a=p.parse_args()
    if a.catalog:print(json.dumps(CATALOG,indent=2));return
    if not a.manifest or not a.output:p.error('manifest and output required')
    specs=json.loads(Path(a.manifest).read_text())
    if not isinstance(specs,list) or not specs:raise ValueError('nonempty exhibit manifest required')
    if len({s['id'] for s in specs})!=len(specs):raise ValueError('duplicate exhibit ID')
    for spec in specs:
        if spec['id'] not in CATALOG:raise ValueError('use catalog exhibit IDs')
        render(spec,Path(a.output)/spec['id'])

if __name__=='__main__':main()
