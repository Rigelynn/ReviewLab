import json,math,random,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data/nsfc_panel_v3'
def read(name):return json.loads((DATA/name).read_text())
def materials():return read('materials.json')
def status():
 data=read('results.json')
 return dict(data,job={'status':'completed','completed':55,'total':55},execution_mode='saved_run_only',human_validation='pending',material_validation='pending')
def kendall(a,b):
    positions={p:i for i,p in enumerate(b)}
    return sum(positions[a[i]]>positions[a[j]] for i in range(len(a)) for j in range(i+1,len(a)))

def local_order(starts,objective):
    cache={}
    def value(seq):
        key=tuple(seq)
        if key not in cache:cache[key]=objective(seq)
        return cache[key]
    best=None;bestval=-math.inf
    for start in starts:
        cur=list(start);val=value(cur)
        for _ in range(30):
            nxt=cur;nv=val
            for i in range(len(cur)):
                for j in range(len(cur)):
                    other=cur.copy();item=other.pop(i);other.insert(j,item);v=value(other)
                    if v>nv+1e-9:nxt,nv=other,v
            if nv<=val+1e-9:break
            cur,val=nxt,nv
        if val>bestval:best,bestval=cur,val
    return best,bestval

def design():
 return {'values':read('researcher_values.json'),'specification':read('design_specification.json'),'audits':read('material_audits.json') if (DATA/'material_audits.json').exists() else {'records':[]}}

def total(r,criteria=None):
 scores=r['parsed']['scores']
 if len(scores)!=3 or any(v.get('score') is None for v in scores):return None
 return round(100*(sum(v['score'] for v in scores)-3)/12,10)

def match_score(e,p):
 keys=sorted(e['field_shares']);a=[e['field_shares'][k] for k in keys];b=[p['field_shares'][k] for k in keys]
 den=math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
 return sum(x*y for x,y in zip(a,b))/den if den else 0

def likelihood_order(order,matrix,rankings,M=12):
 # Same PAVA / Mallows likelihood as the numerical benchmark, score support adapted to 3×1–5 items.
 J=len(matrix);N=len(order);y=[sum(round(M*(1-matrix[e][p]/100)) for e in matrix) for p in order];blocks=[]
 for v in y:
  blocks.append([v,J*M,1])
  while len(blocks)>1 and blocks[-2][0]/blocks[-2][1]>blocks[-1][0]/blocks[-1][1]:
   b=blocks.pop();a=blocks.pop();blocks.append([a[i]+b[i] for i in range(3)])
 probs=[]
 for a,b,n in blocks:probs.extend([min(1-1e-8,max(1e-8,a/b))]*n)
 score_ll=sum(v*math.log(p)+(J*M-v)*math.log1p(-p) for v,p in zip(y,probs))
 K=sum(kendall(r,order) for r in rankings.values());target=K/len(rankings)
 def moments(theta):
  mean=logz=0
  for size in range(1,N+1):
   ex=[math.exp(-theta*k) for k in range(size)];z=sum(ex);logz+=math.log(z);mean+=sum(k*v for k,v in enumerate(ex))/z
  return mean,logz
 lo,hi=0.,30.
 for _ in range(35):
  mid=(lo+hi)/2
  if moments(mid)[0]>target:lo=mid
  else:hi=mid
 theta=(lo+hi)/2
 return score_ll-theta*K-len(rankings)*moments(theta)[1],theta

def rankrate_fits(reverse,ranks,ids,eids):
 packet={'projects':ids,'reviewers':eids,'M':12,'scores':[[reverse[e][p] for p in ids] for e in eids],'rankings':[ranks[e] for e in eids]}
 signature=hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 result=read('rankrate_alignment.json')
 if result['fitting_signature']!=signature:raise ValueError('The saved rankrate fits do not match these evaluations; refitting is required')
 return result

def evaluate(budget=3,threshold=70,include_joint=False,provided=None):
 if type(budget) is not int or not 1<=budget<=9:raise ValueError('Funding capacity must be 1–9')
 if isinstance(threshold,bool) or not isinstance(threshold,(int,float)) or not math.isfinite(threshold) or not 0<=threshold<=100:raise ValueError('Threshold must be 0–100')
 m=materials();res=provided if provided is not None else status();ids=[p['id'] for p in m['projects']];eids=[e['id'] for e in m['experts']]
 matrix={e:{} for e in eids};reverse={e:{} for e in eids};ranks={};recs={e:{} for e in eids}
 for r in res['records']:
  if r['status']!='actual':continue
  if r['task']=='rubric':
   e,p=r['expert_id'],r['project_id'];matrix[e][p]=total(r);recs[e][p]=r['parsed']['funding_recommendation']
   items=[s['score'] for s in r['parsed']['scores']]
   reverse[e][p]=None if any(a is None for a in items) else 15-sum(items)
  elif r['task']=='ranking':ranks[r['expert_id']]=r['parsed']['order']
 missing=sum(matrix[e].get(p) is None for e in eids for p in ids)
 if missing or len(ranks)!=len(eids):return {'status':'incomplete','missing_rubrics':missing,'missing_rankings':len(eids)-len(ranks)}
 lottery=ids.copy();random.Random(1028).shuffle(lottery);tie={p:i for i,p in enumerate(lottery)}
 sort=lambda v:sorted(ids,key=lambda p:(-round(v[p],10),tie[p]))
 J=len(eids);mean={p:math.fsum(matrix[e][p] for e in eids)/J for p in ids}
 # The numerical benchmark uses S/M < 0.5. With M=12, exactly S=6 (T=50) is not approval.
 votes={p:sum(reverse[e][p]<6 for e in eids) for p in ids}
 categoricalvotes={p:sum(recs[e][p]!='do_not_fund' for e in eids) for p in ids}
 numericvotes={p:sum(matrix[e][p]>=threshold for e in eids) for p in ids}
 borda={p:sum(len(ids)-1-ranks[e].index(p) for e in eids) for p in ids}
 derived={e:sort(matrix[e]) for e in eids}
 scoreborda={p:sum(len(ids)-1-derived[e].index(p) for e in eids) for p in ids}
 delegated={p['id']:max(m['experts'],key=lambda e:match_score(e,p))['id'] for p in m['projects']}
 utilities={'Mean score':mean,'Voting (midpoint threshold)':votes,'Ranking (from scores)':scoreborda,'Borda ranking':borda,'Expertise-based delegation':{p:matrix[delegated[p]][p] for p in ids},'Individual (E02)':matrix[eids[1]],'Single reviewer E01 (supplementary)':matrix[eids[0]],'Categorical vote (supplementary)':categoricalvotes,'Score-threshold vote (supplementary)':numericvotes}
 orders={name:sort(u) for name,u in utilities.items()};extras={}
 if include_joint:
  starts=[orders['Mean score'],orders['Borda ranking']]+list(ranks.values())
  order,_=local_order(starts,lambda o:-sum(kendall(r,o) for r in ranks.values()));orders['Rank-only consensus (approximate)']=order
  fitted=rankrate_fits(reverse,ranks,ids,eids)
  for scenario in ['direct','score_derived']:
   for method,fit in fitted['fits'][scenario].items():
    if fit['status']=='completed':
     name='Joint MB · '+method+(' (score-derived ranking)' if scenario=='score_derived' else '')
     orders[name]=fit['order']
  extras={'M':12,'package':'rankrate','version':'1.2.1','solver':'Official FV, Greedy, GreedyLocal and ASTAR; saved R fits matched to the current evaluation fingerprint','fits':fitted['fits'],'new_ai_calls':0}
 # Load hidden values only after every priority order is fixed.
 q={p['project_id']:p['q'] for p in read('researcher_values.json')['projects']};best=sorted(ids,key=lambda p:(-q[p],tie[p]))[:budget];bestval=sum(q[p] for p in best)
 rows=[{'rule':name,'selected':o[:budget],'order':o,'value':round(sum(q[p] for p in o[:budget]),6),'loss':round(bestval-sum(q[p] for p in o[:budget]),6),'loss_per_project':(bestval-sum(q[p] for p in o[:budget]))/budget,'hit_rate':len(set(best)&set(o[:budget]))/budget} for name,o in orders.items()]
 return {'status':'actual_computation','rating_source':res.get('source'),'budget':budget,'threshold':threshold,'matrix':matrix,'reverse_scores':reverse,'rankings':ranks,'recommendations':recs,'utilities':utilities,'vote_counts':votes,'categorical_vote_counts':categoricalvotes,'voting_definition':{'M':12,'reverse_score_strict_upper_bound':6,'total_strict_lower_bound':50,'normalized_condition':'S/M < 0.5'},'delegated_expert':delegated,'rules':rows,'values':q,'best_selected':best,'best_value':bestval,'statistical_diagnostics':extras,'value_status':'Contribution-target coverage derived before review; independent scientific-validity audit pending','ranking_score_disagreement':{e:kendall(sort(matrix[e]),ranks[e]) for e in eids}}
