'use strict';
let sessions = {}, state = null, selected = null;
const $ = id => document.getElementById(id);
function el(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function human(s) { return s.replaceAll('_', ' '); }
function note(message, error=false) { $('message').textContent = message; $('message').className = error ? 'error' : ''; }
async function api(path, body) {
  const headers = {Authorization: 'Bearer ' + sessions[$('role').value]};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const r = await fetch(path, {method: body === undefined ? 'GET' : 'POST', headers, body: body === undefined ? undefined : JSON.stringify(body)});
  const value = await r.json(); if (!r.ok) throw new Error(value.error || 'Request failed'); return value;
}
async function act(path, body, message) { try { await api(path, body); note(message); await refresh(); } catch(e) { note(e.message, true); } }
function latestItems() {
  const latest = {};
  for (const r of state.runs.filter(r=>r.period_id === $('period').value)) if (!latest[r.workflow]) latest[r.workflow] = r.id;
  return state.artifacts.filter(a => ['card_proposal','journal_proposal','close_readiness'].includes(a.kind) && a.run_ids.includes(latest[a.payload.workflow]));
}
function render() {
  const chosen=$('period').value; $('period').replaceChildren(...state.periods.map(p=>{const n=el('option',p.period_id+' · '+p.status);n.value=p.period_id;return n;}));$('period').value=state.periods.some(p=>p.period_id===chosen)?chosen:state.periods.at(-1)?.period_id||'';
  $('scope').textContent = state.scope;
  const items = latestItems();
  $('metrics').replaceChildren(...[
    ['Preparation items', items.length, 'Latest workflow versions'],
    ['Awaiting review', items.filter(a => a.current && a.eligible && a.review_status === 'pending').length, 'Independent human decision'],
    ['Exceptions', items.filter(a => a.blockers.length).length, 'Accounting or evidence needed'],
    ['Reviewed preparation', items.filter(a => a.current && a.review_status === 'approve').length, 'External entries: none']
  ].map(([label, count, caption]) => {const n=el('div', undefined, 'metric');n.append(el('span',label),el('strong',String(count)),el('span',caption));return n;}));
  const latest = {}; state.runs.filter(r=>r.period_id === $('period').value).forEach(r => {if(!latest[r.workflow]) latest[r.workflow]=r;});
  $('runs').replaceChildren(...Object.values(latest).map(r=>{
    const n=el('article',undefined,'run');n.append(el('h3',human(r.workflow)),el('span',human(r.current?r.status:'stale inputs'), 'pill '+(!r.current?'stale':r.status.includes('exceptions')?'warn':'')));
    n.append(el('p','Run '+r.id+' · '+r.steps.filter(s=>s.status==='complete').length+'/'+r.steps.length+' checkpoints'));
    const bar=el('div',undefined,'steps');r.steps.forEach(s=>{const t=el('span',undefined,'step '+s.status);t.title=s.name+': '+s.status+' (attempts '+s.attempts+')';bar.append(t);});n.append(bar);return n;
  }));
  const filtered=items.filter(a => $('filter').value==='all'||($('filter').value==='eligible'?a.eligible&&a.current:a.blockers.length));
  if(!filtered.some(a=>a.id===selected)) selected=filtered[0]?.id;
  $('items').replaceChildren(...filtered.map(a=>{
    const d=a.payload.data, t=d.transaction, n=el('button',undefined,'item'+(a.id===selected?' selected':''));
    const left=el('span'),right=el('span',undefined,'item-right');left.append(el('strong',t?t.description:human(a.kind)),el('span',a.item_key,'small'));
    right.append(el('strong',t?t.currency+' '+t.amount:d.debit_total?'USD '+d.debit_total:'Checklist'),el('span',!a.current?'stale':a.blockers.length?a.blockers.length+' control findings':human(a.review_status),'pill '+(!a.current?'stale':a.blockers.length?'warn':'good')));
    n.append(left,right);n.addEventListener('click',()=>{selected=a.id;render();});return n;
  }));
  if(!filtered.length) $('items').append(el('p','No items in this filter.'));
  renderDetail(filtered.find(a=>a.id===selected));
  $('profile').textContent=JSON.stringify(state.profile,null,2);$('rules').textContent=JSON.stringify(state.rules,null,2);
  $('packages').replaceChildren(...state.packages.filter(p=>p.period_id===$('period').value).map(p=>el('p','Package '+p.id+' · '+p.workflow+' · '+(p.governing?'governing':'historical')+(p.supersedes_package_id?' · replaces '+p.supersedes_package_id:'')+' · '+p.hash)));
  $('finalize').disabled=$('role').value!=='reviewer';
  const areas=[['General Ledger','Journal validation executes; account maintenance, adjustments and posting remain deferred.','Partial'],['Accounts Payable','Vendor/bill/expense/payment module contract; business execution remains deferred.','Deferred'],['Accounts Receivable','Customer/invoice/collection/application/aging module contract; execution remains deferred.','Deferred'],['Banking & Reconciliation','Card preparation executes; banking matches, transfers and reconciliations remain deferred.','Partial'],['Month-End Close','Readiness checklist executes; accruals, adjustment workflows and final close remain deferred.','Partial'],['Financial Reporting','Statements, management reporting, variance analysis and insights remain deferred.','Deferred']];
  $('areas').replaceChildren(...areas.map(([title,desc,status])=>{const n=el('article',undefined,'panel');n.append(el('span',status,'pill'),el('h3',title),el('p',desc));return n;}));
  const table=el('table'),head=el('tr');['Capability','Area','Status','Effect'].forEach(x=>head.append(el('th',x)));table.append(head);state.capabilities.forEach(c=>{const tr=el('tr');[c.id,human(c.area),c.status,c.effect].forEach(x=>tr.append(el('td',x)));table.append(tr);});$('catalog').replaceChildren(table);
  $('sources').replaceChildren(...state.sources.map(s=>{const n=el('details',undefined,'source-row');n.append(el('summary',s.kind+' · '+s.source_key+' · version '+s.version),el('pre',JSON.stringify({snapshot_id:s.id,hash:s.hash,data:s.value},null,2)));return n;}));
  $('audit-events').replaceChildren(...state.audit.map(a=>{const n=el('div',undefined,'audit-row');n.append(el('strong',human(a.event)),el('small',' · '+a.actor+' · '+a.created),el('pre',a.payload));return n;}));
  $('mandates').replaceChildren(...state.occurrences.map(o=>{const n=el('div',undefined,'source-row');n.append(el('strong','Occurrence '+o.id+' · '+human(o.status)),el('p',o.workflow+' · '+o.occurrence_key+(o.reason?' · '+o.reason:'')));return n;}),...state.mandates.map(m=>{const n=el('div',undefined,'source-row');n.append(el('strong','Mandate '+m.id+' · '+human(m.status)),el('p',m.workflows+' · max '+m.max_occurrences+' occurrences'),el('pre',JSON.stringify({period_rule:JSON.parse(m.period_rule),freshness:JSON.parse(m.freshness)},null,2)));const b=el('button','Revoke','secondary');b.disabled=!m.active||$('role').value!=='preparer';b.onclick=()=>act('/api/mandates/revoke',{mandate_id:m.id},'Mandate revoked. Dependent work will be held.');if(m.status==='proposed'){const approve=el('button','Approve mandate');approve.disabled=$('role').value!=='reviewer';approve.onclick=()=>act('/api/mandates/approve',{mandate_id:m.id,reason:'Independent fictional mandate approval'},'Standing authority approved.');n.append(approve);}n.append(b);return n;}));
  ['lock-period','reopen-period','open-period'].forEach(id=>{$(id).disabled=$('role').value!=='reviewer';});
  $('source-exceptions').replaceChildren(...state.source_exceptions.map(e=>el('p',e.source_key+' · '+e.reason+' · '+(e.period_id||'period not configured'),'blocker')),...(state.feed_anomalies||[]).map(e=>el('p',e.source_key+' · '+e.reason+' · '+e.meaning,'blocker')));
  ['run','late','mandate','tick'].forEach(id=>{$(id).disabled=$('role').value!=='preparer';});
}
function renderDetail(a) {
  if(!a){$('detail').replaceChildren(el('p','Select a preparation item.'));return;}
  const data=a.payload.data,t=data.transaction,d=$('detail');d.replaceChildren(el('span',human(a.kind),'eyebrow'),el('h2',t?t.description:a.item_key));
  const dl=el('dl');const pairs=[['Proposed category',data.proposed_category||'No category proposed'],['Vendor',data.vendor?.name||'Not established'],['Review state',a.current?human(a.review_status):'Stale or superseded — re-prepare current inputs'],['Governing item',a.governing?'Yes':'Historical version'],['External result','Not posted / not reconciled / not closed']];
  if(a.kind!=='card_proposal')pairs.splice(0,2,['Debits / credits',(data.debit_total||'—')+' / '+(data.credit_total||'—')]);
  pairs.forEach(([k,v])=>dl.append(el('dt',k),el('dd',v)));d.append(dl);
  if(data.rationale)d.append(el('p',data.rationale,'footnote'));
  a.blockers.forEach(b=>d.append(el('div',human(b),'blocker')));
  if(data.missing_evidence)d.append(el('p','Missing: '+data.missing_evidence.join(', '),'footnote'));
  const details=el('details'),summary=el('summary','Inspect proposal, evidence references and rule versions');details.append(summary,el('pre',JSON.stringify(a.payload,null,2)));d.append(details);
  const evidence=el('details');evidence.append(el('summary','Read supporting source snapshots'));
  (data.evidence||[]).forEach(ref=>{const s=state.sources.find(s=>s.id===ref.snapshot_id);evidence.append(el('pre',JSON.stringify(s?{snapshot_id:s.id,hash:s.hash,value:s.value}:ref,null,2)));});d.append(evidence);
  const reason=el('textarea');reason.placeholder='Record the review finding or decision reason';reason.setAttribute('aria-label','Review reason');reason.rows=2;d.append(reason);
  const actions=el('div',undefined,'actions');['approve','reject','revoke',...(a.review_status==='disputed'||a.review_status==='revoke'?['resolve_approve','resolve_reject']:[])].forEach(decision=>{const b=el('button',decision==='approve'?'Approve preparation':decision==='reject'?'Reject preparation':human(decision),decision==='approve'?'':'secondary');b.disabled=state.periods.some(p=>p.period_id===a.period_id&&p.status==='locked')||$('role').value!=='reviewer'||(decision!=='revoke'&&!a.current)||(decision==='approve'&&!a.eligible);b.onclick=()=>act('/api/review',{artifact_id:a.id,artifact_hash:a.hash,fingerprint:a.fingerprint,decision,reason:reason.value},'Independent decision saved. No external accounting action authorized.');actions.append(b);});d.append(actions);
  const choices={EVIDENCE_REVISED_REQUIRES_REVIEW:['revised_evidence_accepted','refer_external'],POSSIBLE_DUPLICATE:['distinct_purchases','duplicate_of','source_replay'],UNKNOWN_VENDOR:['confirm_vendor'],UNKNOWN_CATEGORY:['code_category'],CREDIT_REQUIRES_REVIEW:['refund_of','standalone_credit'],NON_EXPENSE_REQUIRES_REVIEW:['settlement_of_card_liability','transfer','standalone_credit'],SPLIT_REQUIRES_REVIEW:['allocate'],SOURCE_TRANSITION_REQUIRES_REVIEW:['settlement_verified']};
  for(const code of a.blockers){if(!choices[code]&&code.startsWith('RECEIPT_'))choices[code]=['refer_external'];}
  for(const code of a.blockers.filter(c=>choices[c])){
    const box=el('details');box.append(el('summary','Disposition: '+human(code)));
    const select=el('select');choices[code].forEach(c=>{const o=el('option',human(c));o.value=c;select.append(o);});
    const input=el('textarea');input.placeholder='Decision data as JSON: account_id, allocations, cash_account or duplicate_of as applicable';input.value='{}';
    const save=el('button','Record item disposition');save.disabled=$('role').value!=='reviewer';save.onclick=()=>{try{act('/api/dispositions',{workflow:a.payload.workflow,period_id:a.period_id,item_key:a.item_key,code,choice:select.value,payload:JSON.parse(input.value),evidence:[...(data.evidence||[]),...(data.duplicate_evidence||[])],reason:reason.value},'Disposition saved. Re-prepare, then obtain independent review.');}catch(e){note(e.message,true);}};
    box.append(select,input,save);d.append(box);
  }
  for(const disposition of state.dispositions.filter(x=>x.item_key===a.item_key&&x.action==='apply'&&!state.dispositions.some(r=>r.prior_id===x.id))){const revoke=el('button','Revoke disposition '+disposition.id,'secondary');revoke.disabled=$('role').value!=='reviewer';revoke.onclick=()=>act('/api/dispositions/revoke',{disposition_id:disposition.id,reason:reason.value},'Disposition revoked. Re-prepare for review.');d.append(revoke);}
  if(a.review_status==='disputed')d.append(el('p','Disputed: a third independent human reviewer must explicitly resolve the conflicting decisions. This item is not approved.','blocker'));
  if(a.decisions.length){const hist=el('details');hist.append(el('summary','Decision history ('+a.decisions.length+')'),el('pre',JSON.stringify(a.decisions,null,2)));d.append(hist);}
  d.append(el('p','Approval applies only to this current preparation artifact. Changed inputs require renewed preparation and review.','footnote'));
}
async function refresh(){try{state=await api('/api/state');render();}catch(e){note(e.message,true);}}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('hidden',v.id!==b.dataset.view));document.querySelectorAll('nav button').forEach(n=>n.classList.toggle('active',n===b));$('view-title').textContent=b.textContent;});
$('period').onchange=render;$('role').onchange=render;$('filter').onchange=render;
$('run').onclick=()=>act('/api/run',{workflow:$('workflow').value,period_id:$('period').value},'Workflow queued. The worker will continue preparation.');
$('late').onclick=async()=>{try{const r=await api('/api/demo/late-receipt',{});note(r.changed?'Fictional receipt supplied. Re-prepare the card workflow for renewed review.':'This fictional receipt is already retained. No inputs or approvals changed.');await refresh();}catch(e){note(e.message,true);}};
$('mandate').onclick=()=>act('/api/mandates',{workflows:['journal_preparation'],starts:'2026-11-15T00:00:00+00:00',ends:'2026-11-19T00:00:00+00:00',interval_seconds:86400,max_occurrences:3,period_rule:{kind:'fixed',period_id:$('period').value},freshness:JSON.parse($('mandate-freshness').value)},'Synthetic mandate proposed; independent approval required. Live scheduling remains disabled.');
$('tick').onclick=()=>act('/api/simulate-event',{now:$('sim-time').value},'Simulated occurrence delivered. Repeats return the same run.');
$('export').onclick=async()=>{try{const value=await api('/api/export');const u=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=el('a');a.href=u;a.download='synthetic-accounting-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);note('Synthetic review package exported, including exceptions and evidence history.');}catch(e){note(e.message,true);}};
(async()=>{try{const r=await fetch('/api/session');const data=await r.json();sessions=Object.fromEntries(data.sessions.map(s=>[s.role,s.token]));await refresh();setInterval(async()=>{if(document.activeElement?.tagName!=='TEXTAREA'&&document.activeElement?.tagName!=='INPUT')await refresh();},2500);}catch(e){note(e.message,true);}})();

$('lock-period').onclick=()=>act('/api/periods/lock',{period_id:$('period').value,reason:$('period-reason').value,acknowledgement:$('lock-ack').value||null},'Period locked. Late evidence will be held.');
$('reopen-period').onclick=()=>act('/api/periods/reopen',{period_id:$('period').value,reason:$('period-reason').value},'Period reopened for renewed preparation.');
$('open-period').onclick=()=>act('/api/periods/open',{period_id:$('new-period').value,start:$('period-start').value,end:$('period-end').value,reason:$('period-reason').value},'Fictional accounting period opened.');

$('finalize').onclick=()=>act('/api/packages/finalize',{period_id:$('period').value,workflow:$('workflow').value,reason:$('handover-reason').value,acknowledgement:$('handover-ack').value||null},'Preparation package frozen. No external close or posting.');
