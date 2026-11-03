#!/usr/bin/env python3
"""Figure 18 — print-readable Sankey from the IMMUTABLE Phase A 485-study register.

Creates TWO journal layouts from the same verified data:
  - 2-panel stacked Sankey (recommended for single-column journal printing)
  - 3-stage wide Sankey (optional; use full-page/two-column placement)

Unlike the earlier Plotly version, no ribbon counts are typed into this script.
The raw frozen register is validated by the original v5 verifier functions,
including SHA256, all S9 horizon counts, and Figure 18 final-stage marginals.
Any mismatch stops export; NO synthetic/reconstructed margins are substituted.

Example:
 python Figure18_485_Journal_Readable_Verified.py \\
   --frozen-dir PhaseA_Freeze_Output_WSL/PhaseA_Technical_Corpus_FROZEN_v1_485 \\
   --v5-script verify_and_regenerate_figure18_phaseA_v5.py \\
   --verified-dir Figure18_Verification_485 \\
   --output-dir Figures_485 --dpi 600

Output: two vector PDFs/SVGs, two 600-dpi PNGs, flow/marginal audits, QA receipt.
Requires matplotlib, pandas, numpy and the already-used v5 verifier in project root.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.colors import to_rgb

N = 485
STEM = 'Figure18_485_StudyLevel_VERIFIED_PrintReadable'
ASSET_ORDER = ('Multiple Stocks','Not Reported','Single Stock','Stock Index',
               'Multiple Indices','Cross Market','Portfolio')
HORIZON_ORDER = ('Horizon not reported','Single reported horizon','Multiple horizons')
UTILITY_ORDER = ('Neither established','Economic only','Robustness only',
                 'Economic + robustness')
ASSET_COLORS = ('#2C7FB8','#A7BFDF','#F2B36D','#8ED081','#F08C8A',
                '#B7A6D9','#9A6A46')
HORIZON_COLORS = ('#2C7FB8','#A7BFDF','#F2B36D')
UTILITY_COLORS = ('#2C7FB8','#A7BFDF','#F2B36D','#8ED081')


def args_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--frozen-dir', type=Path, required=True)
    p.add_argument('--v5-script', type=Path, default=Path('verify_and_regenerate_figure18_phaseA_v5.py'))
    p.add_argument('--verified-dir', type=Path,
                   help='Optional: compare recomputed study-level flows to v5 audit CSVs and receipt')
    p.add_argument('--output-dir', type=Path, default=Path('Figures_485'))
    p.add_argument('--dpi', type=int, default=600)
    return p.parse_args()


def import_v5(path):
    if not path.is_file():
        raise FileNotFoundError(f'Figure 18 v5 verifier not found at {path}; copy it into project root')
    spec = importlib.util.spec_from_file_location('figure18_v5_lock', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def source_flows(m, source):
    rows, columns, source_sha = m.read_frozen(source)
    required = ['Paper_ID','Asset_Scope','Forecast_Horizon','Economic_Evaluation',
                'Regime_Specific_Evaluation','Shock_Period_Evaluation']
    missing = set(required)-set(columns)
    if missing:
        raise RuntimeError(f'Missing required frozen fields: {sorted(missing)}')
    m.audit_horizon_source_codes(rows, 'Forecast_Horizon')
    stage1 = Counter()
    stage2 = Counter()
    triplets = Counter()
    assets = Counter(); horizons = Counter(); utility = Counter()
    counts = Counter()
    for r in rows:
        pid=r['Paper_ID'].strip()
        a=m.normalize_asset(r['Asset_Scope'],pid)
        h=m.normalize_horizon(r['Forecast_Horizon'],pid)
        econ=m.confirmed_yes(r['Economic_Evaluation'],pid,'Economic_Evaluation')
        regime=m.confirmed_yes(r['Regime_Specific_Evaluation'],pid,'Regime_Specific_Evaluation')
        shock=m.confirmed_yes(r['Shock_Period_Evaluation'],pid,'Shock_Period_Evaluation')
        robust=regime or shock
        dest=('Economic + robustness' if econ and robust else 'Economic only' if econ else
              'Robustness only' if robust else 'Neither established')
        assets[a]+=1; horizons[h]+=1; utility[dest]+=1
        stage1[a,h]+=1; stage2[h,dest]+=1; triplets[a,h,dest]+=1
        counts['Economic_Evaluation=Yes']+=int(econ)
        counts['Regime_Specific_Evaluation=Yes']+=int(regime)
        counts['Shock_Period_Evaluation=Yes']+=int(shock)
        counts['Regime_OR_Shock=Yes']+=int(robust)
        counts['Economic_AND_Robust=Yes']+=int(econ and robust)
    m.compare_exact(m.ASSET_COUNTS, assets, 'Figure18 print layout: asset scope')
    m.compare_exact(m.HORIZON_COUNTS, horizons, 'Figure18 print layout: horizon')
    m.compare_exact(m.UTILITY_COUNTS, utility, 'Figure18 print layout: final stage')
    m.compare_exact({'Economic_Evaluation=Yes':37,
                     'Regime_Specific_Evaluation=Yes':8,
                     'Shock_Period_Evaluation=Yes':15,
                     'Regime_OR_Shock=Yes':20,
                     'Economic_AND_Robust=Yes':1},counts,'Figure18 print layout: evidence components')
    if sum(stage1.values())!=N or sum(stage2.values())!=N or sum(triplets.values())!=N:
        raise RuntimeError('Study-level flows do not conserve 485 records')
    return stage1,stage2,triplets,assets,horizons,utility,source_sha


def verify_existing_audit(folder, s1, s2, sha):
    if not folder:
        return 'not_requested'
    receipt=folder/'Figure18_Flow_Verification_Receipt_v5.json'
    if not receipt.is_file():
        raise FileNotFoundError(f'Existing verification receipt missing: {receipt}')
    x=json.loads(receipt.read_text(encoding='utf-8-sig'))
    if (x.get('status')!='FULL_FLOW_STUDY_LEVEL_VERIFIED_FROM_FROZEN_REGIME_SHOCK_FIELDS'
            or x.get('frozen_sha256')!=sha or x.get('stage1_total')!=485
            or x.get('stage2_total')!=485):
        raise RuntimeError('Existing v5 receipt does not authenticate this frozen register')
    for name, key_src, key_dst, expected in (
        ('Figure18_Verified_Asset_to_Horizon.csv','Asset','Horizon',s1),
        ('Figure18_Verified_Horizon_to_FinalStage.csv','Horizon','Final_Category',s2),
    ):
        csvpath=folder/name
        if not csvpath.is_file():
            raise FileNotFoundError(f'Existing v5 audit CSV missing: {csvpath}')
        with csvpath.open(newline='',encoding='utf-8-sig') as fh:
            rec=list(csv.DictReader(fh))
        actual=Counter()
        for row in rec:
            k=(row[key_src],row[key_dst]); value=int(row['Studies'])
            if k in actual or value<0:
                raise RuntimeError(f'Duplicate/invalid v5 link {k!r} in {name}')
            actual[k]=value
        if actual!=expected:
            differing={k:(actual.get(k,0),expected.get(k,0)) for k in set(actual)|set(expected)
                       if actual.get(k,0)!=expected.get(k,0)}
            raise RuntimeError(f'Frozen register and v5 flow CSV disagree: {name}: {differing}')
    print('PASS: both flow matrices match previous v5 audit receipt and CSVs')
    return 'matched_v5_receipt_and_csvs'


def rgba(hex_color,alpha):
    return (*to_rgb(hex_color),alpha)


def nodes(order,values, top=.935, bottom=.075, min_gap=.018):
    n=len(order)
    # Same unit scale for BOTH sides. Additional whitespace is distributed between nodes,
    # never by changing the numeric area of their bar or ribbon.
    usable=top-bottom
    gap=min_gap if n>1 else 0
    unit=(usable - (n-1)*gap)/N
    if unit<=0: raise RuntimeError('Node spacing exceeds available area')
    spans={}
    y=top
    for label in order:
        height=values[label]*unit
        spans[label]=(y-height,y)
        y=y-height-gap
    return spans,unit


def shared_scale_nodes(left_order,right_order,left_total,right_total, top=.940, bottom=.075,
                       gapL=.018,gapR=.038):
    nL=len(left_order);nR=len(right_order)
    # Choose a common scale for both columns so the width of each ribbon is quantitatively correct.
    unit=min((top-bottom-(nL-1)*gapL)/N,(top-bottom-(nR-1)*gapR)/N)
    if unit<=0:raise RuntimeError('Invalid common node scale')
    def build(order,vals,gap):
        heights={k:vals[k]*unit for k in order}
        occupied=sum(heights.values())+gap*(len(order)-1)
        y=(top+bottom+occupied)/2
        spans={}
        for k in order:
            spans[k]=(y-heights[k],y)
            y-=heights[k]+gap
        return spans
    return build(left_order,left_total,gapL),build(right_order,right_total,gapR),unit


def relax_labels(spans,order,low=.075,high=.95,min_sep=.044):
    # Decouple label location from data glyph only when needed for legibility;
    # do NOT add pointer arrows or misstate data.
    from itertools import groupby
    y={k:sum(spans[k])/2 for k in order}
    # top to bottom, then propagate upward when collisions exist.
    labels=[y[k] for k in order]
    for i in range(1,len(labels)):
        labels[i]=min(labels[i],labels[i-1]-min_sep)
    if labels[-1]<low:
        shift=low-labels[-1]
        labels=[z+shift for z in labels]
    if labels[0]>high:
        shift=labels[0]-high
        labels=[z-shift for z in labels]
    if labels[-1]<low-1e-5:
        raise RuntimeError('Not enough height for readable labels')
    return dict(zip(order,labels))


def draw_ribbon(ax,x0,x1,from_top,from_bottom,to_top,to_bottom,color,alpha):
    d=(x1-x0)*.52
    verts=[(x0,from_top),(x0+d,from_top),(x1-d,to_top),(x1,to_top),
           (x1,to_bottom),(x1-d,to_bottom),(x0+d,from_bottom),(x0,from_bottom),(x0,from_top)]
    codes=[MPath.MOVETO,MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.LINETO,
           MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.CLOSEPOLY]
    patch=PathPatch(MPath(verts,codes),facecolor=rgba(color,alpha),edgecolor='none',lw=0,zorder=2)
    ax.add_patch(patch)


def draw_stage(ax, stage, left_order,right_order,left_counts,right_counts,links,
               left_colors,right_colors,left_x=.38,right_x=.615,labelsize=15):
    # Normalize pair: exact shared scale and very thin white separators.
    gapL=.023 if len(left_order)>=6 else .055
    gapR=.055 if len(right_order)<=4 else .020
    left,right,unit=shared_scale_nodes(left_order,right_order,left_counts,right_counts,
                                       gapL=gapL,gapR=gapR)
    node_w=.016
    src_stack={k:left[k][1] for k in left_order}
    dst_stack={k:right[k][1] for k in right_order}
    cdict=dict(zip(left_order,left_colors))
    # Source order, then destination order, deterministic study-derived ribbons.
    for lk in left_order:
        for rk in right_order:
            count=links.get((lk,rk),0)
            if count<=0:continue
            dh=count*unit
            fy1=src_stack[lk];fy0=fy1-dh;src_stack[lk]=fy0
            ty1=dst_stack[rk];ty0=ty1-dh;dst_stack[rk]=ty0
            draw_ribbon(ax,left_x+node_w/2,right_x-node_w/2,
                        fy1,fy0,ty1,ty0,cdict[lk],.32 if stage=='A' else .31)
    # Numerical closure at node level (within machine tolerance).
    for k in left_order:
        if abs(src_stack[k]-left[k][0])>1e-9:
            raise RuntimeError(f'Source ribbon sum mismatch for {k}')
    for k in right_order:
        if abs(dst_stack[k]-right[k][0])>1e-9:
            raise RuntimeError(f'Destination ribbon sum mismatch for {k}')
    for order, spans, colors,x in [(left_order,left,left_colors,left_x),
                                  (right_order,right,right_colors,right_x)]:
        for k,c in zip(order,colors):
            lo,hi=spans[k]
            ax.add_patch(Rectangle((x-node_w/2,lo),node_w,hi-lo,
                            facecolor=c,edgecolor='#676767',linewidth=.55,zorder=4))
    # Print-sized serif text, single-line labels, no pointers.
    for order,spans,counts,x,ha in (
        (left_order,left,left_counts,left_x-.019,'right'),
        (right_order,right,right_counts,right_x+.019,'left'),
    ):
        pos=relax_labels(spans,order,min_sep=.060 if len(order)>5 else .085,
                         low=.048,high=.95)
        for k in order:
            ax.text(x,pos[k],f'{k} ({counts[k]})',ha=ha,va='center',
                    fontsize=labelsize,color='#252525',zorder=6,
                    path_effects=[])
    ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')


def figure_stacked(s1,s2,assets,horizons,utilities):
    fig=plt.figure(figsize=(10.5,8.35),facecolor='white')
    axes=fig.add_gridspec(2,1,left=.025,right=.975,top=.92,bottom=.07,
                         height_ratios=[1.17,1],hspace=.27)
    a=fig.add_subplot(axes[0,0]);b=fig.add_subplot(axes[1,0])
    a.set_title('A. Asset scope to forecast-horizon reporting',fontweight='bold',
                fontsize=18,loc='center',pad=8)
    b.set_title('B. Forecast-horizon reporting to economic / regime-shock evidence',
                fontweight='bold',fontsize=18,loc='center',pad=8)
    draw_stage(a,'A',ASSET_ORDER,HORIZON_ORDER,assets,horizons,s1,
               ASSET_COLORS,HORIZON_COLORS,labelsize=16.2)
    draw_stage(b,'B',HORIZON_ORDER,UTILITY_ORDER,horizons,utilities,s2,
               HORIZON_COLORS,UTILITY_COLORS,labelsize=16.2)
    # Intentional no super-title, footnote or tiny embedded text. Caption belongs in LaTeX.
    return fig


def figure_wide(s1,s2,assets,horizons,utilities):
    # One continuous 3-stage layout; recommended ONLY at full two-column/page width.
    from matplotlib.gridspec import GridSpec
    fig=plt.figure(figsize=(15.4,6.1),facecolor='white')
    ax=fig.add_axes([.025,.06,.95,.84]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
    colors=[ASSET_COLORS,HORIZON_COLORS,UTILITY_COLORS]
    groups=[ASSET_ORDER,HORIZON_ORDER,UTILITY_ORDER]
    vals=[assets,horizons,utilities]
    xs=[.235,.525,.765];node_w=.012
    gaps=[.023,.055,.062]
    # shared scale across all three stages
    top=.95;bottom=.06
    unit=min((top-bottom-(len(g)-1)*gp)/N for g,gp in zip(groups,gaps))
    spans=[]
    for order,counts,gap in zip(groups,vals,gaps):
        occupied=N*unit+(len(order)-1)*gap
        y=(top+bottom+occupied)/2
        s={}
        for k in order:
            dh=counts[k]*unit;s[k]=(y-dh,y);y-=dh+gap
        spans.append(s)
    for j,links in enumerate((s1,s2)):
        src={k:spans[j][k][1] for k in groups[j]}
        dst={k:spans[j+1][k][1] for k in groups[j+1]}
        for k in groups[j]:
            for k2 in groups[j+1]:
                n=links.get((k,k2),0)
                if n==0:continue
                dh=n*unit;f1=src[k];src[k]-=dh;t1=dst[k2];dst[k2]-=dh
                draw_ribbon(ax,xs[j]+node_w/2,xs[j+1]-node_w/2,
                            f1,src[k],t1,dst[k2],colors[j][groups[j].index(k)],.31)
    for j,order in enumerate(groups):
        for k,c in zip(order,colors[j]):
            l,h=spans[j][k]
            ax.add_patch(Rectangle((xs[j]-node_w/2,l),node_w,h-l,
                                   facecolor=c,edgecolor='#676767',lw=.48,zorder=4))
    for j,order in enumerate(groups):
        pos=relax_labels(spans[j],order,min_sep=.058 if len(order)>5 else .090,
                         low=.035,high=.96)
        for k in order:
            if j==0:x=xs[j]-.011;ha='right'
            else:x=xs[j]+.011;ha='left'
            ax.text(x,pos[k],f'{k} ({vals[j][k]})',fontsize=15.3,
                    ha=ha,va='center',color='#282828',zorder=7)
    for x,t in zip(xs,('Asset scope','Horizon','Evaluated utility')):
        fig.text(.025+.95*x,.955,t,ha='center',va='center',fontsize=18.2,
                 fontweight='bold',color='#242424')
    return fig


def save(fig,stem,outdir,dpi):
    out=[]
    for ext in ('pdf','svg','png'):
        dst=outdir/f'{stem}.{ext}'
        kwargs={'format':ext,'facecolor':'white'}
        if ext=='png': kwargs['dpi']=dpi
        fig.savefig(dst,**kwargs)
        out.append(dst)
    plt.close(fig)
    return out


def main():
    args=args_parser()
    if args.dpi<100:raise ValueError('dpi must be >=100; 600 recommended')
    if args.output_dir.resolve()==args.frozen_dir.resolve():
        raise ValueError('Refusing to write outputs within frozen register directory')
    m=import_v5(args.v5_script)
    s1,s2,triplets,a,h,u,sha=source_flows(m,args.frozen_dir)
    prior=verify_existing_audit(args.verified_dir,s1,s2,sha)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'serif',
                         'font.serif':['Times New Roman','STIXGeneral','DejaVu Serif'],
                         'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
                         'axes.unicode_minus':False})
    result=[]
    result+=save(figure_stacked(s1,s2,a,h,u), STEM+'_TwoPanel',args.output_dir,args.dpi)
    result+=save(figure_wide(s1,s2,a,h,u), STEM+'_Wide3Stage',args.output_dir,args.dpi)
    m.write_csv(args.output_dir/'Figure18_PrintReadable_Stage1.csv',
                ['Asset','Horizon','Studies'],
                [{'Asset':x,'Horizon':y,'Studies':n} for (x,y),n in sorted(s1.items())])
    m.write_csv(args.output_dir/'Figure18_PrintReadable_Stage2.csv',
                ['Horizon','Final_Category','Studies'],
                [{'Horizon':x,'Final_Category':y,'Studies':n} for (x,y),n in sorted(s2.items())])
    qa={'status':'PASS_VERIFIED_STUDY_LEVEL_PRINT_READABLE','n_studies':N,
        'source_sha256':sha,'compared_with_v5_audit':prior,
        'stage1_n':sum(s1.values()),'stage2_n':sum(s2.values()),
        'stage1_edges':len(s1),'stage2_edges':len(s2),
        'evidence_definition':'Regime_Specific_Evaluation=Yes OR Shock_Period_Evaluation=Yes',
        'asset_totals':dict(a),'horizon_totals':dict(h),'utility_totals':dict(u),
        'files':[x.name for x in result]}
    (args.output_dir/'Figure18_PrintReadable_QA.json').write_text(
        json.dumps(qa,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('PASS: PDF and SVG preserve vector fonts and exact verified study-level ribbons')
    print('Frozen source SHA256:',sha)
    for x in result: print(' ',x)
    print('Preferred for single manuscript text width:',STEM+'_TwoPanel.pdf')
    print('Alternative for page-wide figure*:',STEM+'_Wide3Stage.pdf')

if __name__=='__main__':
    main()
