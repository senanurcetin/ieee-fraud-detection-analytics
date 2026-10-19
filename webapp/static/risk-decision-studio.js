/* Independent NEXUS Risk Decision Studio.
 * No reuse of the prior dashboard DOM, legacy chart renderer, or CSS.
 * Displays ONLY numbers present in /api/dashboard; empty states stay explicit.
 */
(() => {
  'use strict';
  const $=id=>document.getElementById(id),state={data:null,view:'overview'};
  const views=['overview','trend','amount','customer','proxy','behavior','features','model','insights'];
  const num=v=>Number.isFinite(Number(v))?Number(v):0;
  const fmt=(v,d=2)=>v===null||v===undefined||!Number.isFinite(Number(v))?'—':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
  const pct=v=>v===null||v===undefined?'—':fmt(num(v)*100,2)+'%';
  const money=v=>v===null||v===undefined?'—':'$'+(Math.abs(num(v))>=1e6?fmt(num(v)/1e6,2)+'M':Math.abs(num(v))>=1e3?fmt(num(v)/1e3,2)+'K':fmt(v,0));
  const el=(tag,className='',content='')=>{const e=document.createElement(tag);e.className=className;e.textContent=String(content??'');return e};
  const text=(id,v)=>{$(id).textContent=String(v??'—')};
  const get=key=>Array.isArray(state.data?.[key])?state.data[key]:[];
  const agg=(rows,key)=>rows.reduce((sum,row)=>sum+num(row[key]),0);
  const mean=(rows,key)=>rows.length?agg(rows,key)/rows.length:0;
  const metric=(label,value,note)=>({label,value,note});
  function defineView(id) {
    const k=get('executive_kpis')[0]||{};
    const overview={
      name:'Exposure overview',eyebrow:'Executive overview / measured exposure',
      title:'Understand the fraud surface before intervening.',
      lede:'Portfolio concentration, observed loss exposure and the segments worth investigating. Grounded in the reporting snapshot, never invented customer events.',
      main:'product_risk',mainLabel:r=>'Product '+(r.product_cd||'Unknown'),value:r=>r.fraud_rate,form:pct,
      secondary:'segment_watchlist',secondaryLabel:r=>(r.segment_family||'Segment')+' / '+(r.segment_name||'Unknown'),secondaryValue:r=>r.fraud_share,secondaryForm:pct,
      chartTitle:'Observed fraud rate by product',detailTitle:'Concentrated risk signals',
      insight:'Relative fraud rate and total loss exposure are different signals. Avoid labeling a high-rate niche as the highest-dollar risk without checking its absolute amounts.',
      boundary:'Products are masked IEEE-CIS groups. Their codes do not identify real companies or customers.',
      metrics:[metric('Reported transactions',fmt(k.total_transactions,0),'Source portfolio'),metric('Observed fraud rate',pct(k.fraud_rate),'Fraud / transactions'),metric('Observed fraud amount',money(k.fraud_transaction_amount),'Labeled transaction amount'),metric('Fraud transactions',fmt(k.fraud_transactions,0),'Recorded positive labels')]
    };
    if(id==='overview')return overview;
    const generic=(data)=>({...overview,...data});
    if(id==='trend'){
      const rows=get('daily_drift'),last=rows.at(-1)||{};
      return generic({name:'Time & drift',eyebrow:'Behavior change / relative time',title:'Find the periods where risk changes shape.',
        lede:'Relative TransactionDT day movement, not calendar seasonality. Read rate changes alongside transaction counts to avoid false alarm narratives.',
        main:'daily_drift',mainLabel:r=>'Day '+r.transaction_day,value:r=>r.fraud_rate,form:pct,
        secondary:'daily_drift',secondaryLabel:r=>'Day '+r.transaction_day,secondaryValue:r=>r.fraud_count,secondaryForm:v=>fmt(v,0),
        chartTitle:'Daily fraud rate (relative time)',detailTitle:'Fraud count by relative day',
        insight:'A rising fraud rate without transaction-volume context can exaggerate operational significance.',
        boundary:'Relative TransactionDT does not establish weekdays, seasons or a real calendar date.',
        metrics:[metric('Relative periods',fmt(rows.length,0),'Observed reporting days'),metric('Latest fraud rate',pct(last.fraud_rate),'Last reported relative period'),metric('Mean daily fraud rate',pct(mean(rows,'fraud_rate')),'Unweighted mean of periods'),metric('Fraud labels',fmt(agg(rows,'fraud_count'),0),'Across available reporting periods')]});
    }
    if(id==='amount'){
      const rows=get('amount_bands');
      return generic({name:'Transaction value',eyebrow:'Financial loss / amount bands',title:'Separate transaction frequency from loss exposure.',
        lede:'Transaction-value groups by observed fraud amount, with rate context and transparent denominators.',
        main:'amount_bands',mainLabel:r=>r.amount_band,value:r=>r.fraud_transaction_amount,form:money,
        secondary:'amount_bands',secondaryLabel:r=>r.amount_band,secondaryValue:r=>r.fraud_rate,secondaryForm:pct,
        chartTitle:'Observed fraud amount by value band',detailTitle:'Fraud rate by amount band',
        insight:'High-dollar exposure and high fraud rate need not occur in the same amount range.',
        boundary:'Fraud amount is observed on labeled transactions; unobserved downstream chargeback costs are not in IEEE-CIS.',
        metrics:[metric('Amount bands',fmt(rows.length,0),'Reported groups'),metric('Observed fraud amount',money(agg(rows,'fraud_transaction_amount')),'Sum across disjoint amount ranges'),metric('Observed fraud labels',fmt(agg(rows,'fraud_count'),0),'Sum across amount groups'),metric('Highest amount',money(Math.max(...rows.map(r=>num(r.avg_transaction_amount)),0)),'Highest group mean, not single transaction')]});
    }
    if(id==='customer'){
      const rows=get('identity_risk');
      return generic({name:'Identity signals',eyebrow:'Masked customer / identity metadata',title:'Diagnose identity coverage without profiling people.',
        lede:'Observed fraud rates in masked identity-presence cohorts and available email-domain group proxies.',
        main:'identity_risk',mainLabel:r=>r.identity_segment||String(r.has_identity),value:r=>r.fraud_rate,form:pct,
        secondary:'email_domain_risk',secondaryLabel:r=>r.purchaser_email_group,secondaryValue:r=>r.fraud_rate,secondaryForm:pct,
        chartTitle:'Identity availability vs fraud rate',detailTitle:'Email group risk comparison',
        insight:'Identity coverage is both a risk signal and a missing-data property. Correlation does not establish individual intent.',
        boundary:'No real person names or identities are available; use only masked proxy groups.',
        metrics:[metric('Identity groups',fmt(rows.length,0),'Observed segments'),metric('Transactions with identity',fmt(rows.find(r=>r.has_identity===1)?.transaction_count,0),'Presence cohort'),metric('Identity coverage',pct(k.identity_coverage_rate),'All transactions'),metric('Portfolio baseline',pct(k.fraud_rate),'Context for cohort rates')]});
    }
    if(id==='proxy'){
      const rows=get('proxy_signal_risk');
      return generic({name:'Masked proxies',eyebrow:'Address/distance proxies / not geography',title:'Read masked location signals with precision.',
        lede:'An investigative view of address and distance proxies. There are no verified country, latitude, city or IP dimensions in the source.',
        main:'proxy_signal_risk',mainLabel:r=>r.proxy_segment,value:r=>r.fraud_rate,form:pct,
        secondary:'proxy_signal_risk',secondaryLabel:r=>r.proxy_segment,secondaryValue:r=>r.fraud_share,secondaryForm:pct,
        chartTitle:'Masked-proxy fraud rate',detailTitle:'Observed fraud share within segments',
        insight:'Some proxy cohorts overlap. Their fraud shares cannot be summed into a total.',
        boundary:'This is NOT geographic mapping. External enrichment would be required for city or country claims.',
        metrics:[metric('Proxy cohorts',fmt(rows.length,0),'Reported segments'),metric('Highest cohort rate',pct(Math.max(...rows.map(r=>num(r.fraud_rate)),0)),'Observed maximum'),metric('Portfolio fraud rate',pct(k.fraud_rate),'Reference denominator'),metric('Geolocation fields','0','Verified country/city/IP dimensions')]});
    }
    if(id==='behavior'){
      const rows=get('payment_heatmap');
      return generic({name:'Payment behavior',eyebrow:'Transactions / payment signals',title:'Locate risk at the payment intersection.',
        lede:'Payment-card network and type cohorts, complemented by available behavioral patterns.',
        main:'payment_heatmap',mainLabel:r=>(r.card_network||'Unknown')+' / '+(r.card_type||'Unknown'),value:r=>r.fraud_rate,form:pct,
        secondary:'time_amount_signals',secondaryLabel:r=>'Relative hour '+(r.transaction_hour??'—')+' / '+(r.amount_decimal_group||''),secondaryValue:r=>r.fraud_rate,secondaryForm:pct,
        chartTitle:'Payment-method fraud rates',detailTitle:'Relative-hour behavioral signals',
        insight:'Masked categorical intersections identify investigation queues, not causally proven fraud mechanisms.',
        boundary:'Relative transaction hours are not evidence about actual customer time zones.',
        metrics:[metric('Payment cohorts',fmt(rows.length,0),'Reported combinations'),metric('Payment peak rate',pct(Math.max(...rows.map(r=>num(r.fraud_rate)),0)),'Maximum cohort rate'),metric('Time/amount cells',fmt(get('time_amount_signals').length,0),'Available matrix entries'),metric('Portfolio baseline',pct(k.fraud_rate),'All transactions')]});
    }
    if(id==='features'){
      const rows=get('feature_importance');
      return generic({name:'Feature drivers',eyebrow:'Model explanation / measured importance',title:'Understand which variables influence the ranking.',
        lede:'Feature and family analysis without treating statistical importance as causal proof.',
        main:'feature_importance',mainLabel:r=>r.feature,value:r=>r.importance,form:v=>fmt(v,0),
        secondary:'data_quality',secondaryLabel:r=>r.feature_family,secondaryValue:r=>r.avg_missing_rate,secondaryForm:pct,
        chartTitle:'Feature importance ranking',detailTitle:'Missingness by feature family',
        insight:'High importance with high missingness is a monitoring concern; it is not evidence of a causal effect.',
        boundary:'Many engineered IEEE-CIS variables are masked. Labels cannot be interpreted as known business attributes.',
        metrics:[metric('Ranked features',fmt(rows.length,0),'Reported model drivers'),metric('Largest importance',fmt(Math.max(...rows.map(r=>num(r.importance)),0),0),'Model-native importance'),metric('Data-quality families',fmt(get('data_quality').length,0),'Reported source groups'),metric('Interpretation','Associative','Causal attribution not established')]});
    }
    if(id==='model'){
      const rows=get('validation_risk_bands'),thresholds=get('validation_threshold_simulation'),mid=thresholds.find(r=>Math.abs(num(r.score_threshold)-.5)<.001)||thresholds[Math.floor(thresholds.length/2)]||{};
      return generic({name:'Model governance',eyebrow:'Holdout / evaluation quality',title:'Make the cost of each operating threshold visible.',
        lede:'Validation-only evidence for capture, review capacity and precision. Ranking scores are not automatically calibrated probabilities.',
        main:'validation_risk_bands',mainLabel:r=>r.risk_band,value:r=>r.observed_fraud_rate,form:pct,
        secondary:'model_calibration',secondaryLabel:r=>'Score decile '+r.score_decile,secondaryValue:r=>r.observed_fraud_rate,secondaryForm:pct,
        chartTitle:'Holdout fraud rate by model band',detailTitle:'Observed fraud by score decile',
        insight:'Threshold policy must balance captured fraud, review burden and false positives on the same validation population.',
        boundary:'Model output is a prioritization tool and needs calibration, drift monitoring and human control.',
        metrics:[metric('Threshold points',fmt(thresholds.length,0),'Measured holdout simulations'),metric('Capture @ '+fmt(mid.score_threshold,2),pct(mid.fraud_capture_rate),'Holdout fraud labels'),metric('Precision @ threshold',pct(mid.precision_rate),'Holdout flagged cases'),metric('Review workload',pct(mid.workload_share),'Holdout transaction share')]});
    }
    if(id==='insights'){
      const rows=get('segment_watchlist');
      return generic({name:'Priority actions',eyebrow:'Decision queue / overlapping risk signals',title:'Turn evidence into a prioritized review agenda.',
        lede:'A segment-watchlist investigation surface, ordered by fraud concentration and requiring validation before policy changes.',
        main:'segment_watchlist',mainLabel:r=>(r.segment_family||'Segment')+' / '+(r.segment_name||'Unknown'),value:r=>r.fraud_share,form:pct,
        secondary:'segment_watchlist',secondaryLabel:r=>(r.segment_family||'Segment')+' / '+(r.segment_name||'Unknown'),secondaryValue:r=>r.lift,secondaryForm:v=>fmt(v,2)+'×',
        chartTitle:'Fraud share by watched segment',detailTitle:'Lift over portfolio baseline',
        insight:'Prioritize overlap-aware targeted policies and evaluate operational review costs before automatic blocking.',
        boundary:'Watchlist segments overlap; fraud shares must never be accumulated as a waterfall or a cumulative Pareto.',
        metrics:[metric('Review segments',fmt(rows.length,0),'Measured watchlist cuts'),metric('Baseline fraud rate',pct(k.fraud_rate),'Portfolio reference'),metric('Total fraud labels',fmt(k.fraud_transactions,0),'Observed labels'),metric('Execution status','Recommendation','No automated decision executed')]});
    }
    return overview;
  }
  const setTab=(name)=>{
    document.querySelectorAll('[data-tab]').forEach(button=>{
      const selected=button.dataset.tab===name;
      button.setAttribute('aria-selected',selected?'true':'false');
      button.tabIndex=selected?0:-1;
      $('panel-'+button.dataset.tab).hidden=!selected;
    });
  };
  const titleCase=s=>String(s??'Unknown');
  function normalizedRows(dataset,label,value){
    return get(dataset).filter(row=>label(row)!=null && value(row)!=null && Number.isFinite(Number(value(row))))
      .map(row=>({row,label:titleCase(label(row)),value:num(value(row))}))
      .sort((a,b)=>b.value-a.value).slice(0,12);
  }
  function makeBars(root,rows,format,caption){
    if(!rows.length){root.replaceChildren(el('p','evidence-note','No reported metric for this slice.'));return;}
    const max=Math.max(...rows.map(x=>Math.max(0,x.value)),.0001);
    root.replaceChildren(...rows.map((item,index)=>{
      const div=el('div','chart-row');div.setAttribute('role','button');div.setAttribute('tabindex','0');
      div.setAttribute('aria-label',item.label+': '+format(item.value));
      const label=el('span','chart-label',item.label),track=el('div','chart-track');
      const bar=el('span',index===0?'best':'');bar.style.width=Math.max(0,Math.min(100,item.value/max*100))+'%';track.append(bar);
      const value=el('strong','chart-value',format(item.value));
      div.append(label,track,value);
      const show=()=>{const target=$('selected-detail');target.replaceChildren(el('strong','',item.label),el('span','',format(item.value)+' · '+caption));};
      div.addEventListener('click',show);
      div.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show();}});
      return div;
    }));
  }
  function renderMetrics(metrics){$('metric-grid').replaceChildren(...metrics.map(m=>{const elx=el('article','metric');elx.append(el('div','metric-label',m.label),el('div','metric-value',m.value),el('div','metric-note',m.note));return elx;}));}
  function renderTable(rows,formatter){
    const table=el('table','data-table');const head=el('thead'),hrow=el('tr');
    ['Segment','Observed value'].forEach(label=>hrow.append(el('th','',label)));head.append(hrow);
    const tbody=el('tbody');
    rows.forEach(item=>{const tr=el('tr');tr.append(el('td','',item.label),el('td','',formatter(item.value)));tbody.append(tr);});
    table.append(head,tbody);$('benchmark-table').replaceChildren(table);
  }
  function renderLine(rows){
    const holder=$('brief-chart');
    const data=rows.filter(x=>Number.isFinite(x.value)).slice(-180);
    if(data.length<2)return;
    const w=780,h=330,pl=48,pr=25,pt=34,pb=45,max=Math.max(...data.map(x=>x.value),.0001)*1.1;
    const x=i=>pl+i/Math.max(data.length-1,1)*(w-pl-pr),y=v=>h-pb-v/max*(h-pt-pb);
    const ns='http://www.w3.org/2000/svg';
    const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 '+w+' '+h);
    svg.setAttribute('role','img');svg.setAttribute('aria-label','Observed fraud rate trend across relative days');
    svg.style.cssText='width:100%;height:auto;display:block';
    const ticks=[0,.25,.5,.75,1].map(fr=>{const group=document.createElementNS(ns,'g');const ln=document.createElementNS(ns,'line');ln.setAttribute('x1',pl);ln.setAttribute('x2',w-pr);ln.setAttribute('y1',y(max*fr));ln.setAttribute('y2',y(max*fr));ln.setAttribute('stroke','#e4eaf3');group.append(ln);const label=document.createElementNS(ns,'text');label.setAttribute('x',pl-8);label.setAttribute('y',y(max*fr)+4);label.setAttribute('text-anchor','end');label.setAttribute('font-size','11');label.setAttribute('fill','#6a839b');label.textContent=pct(max*fr);group.append(label);return group;});
    const path=document.createElementNS(ns,'polyline');path.setAttribute('points',data.map((r,i)=>x(i)+','+y(r.value)).join(' '));path.setAttribute('fill','none');path.setAttribute('stroke','#5b71bf');path.setAttribute('stroke-width','3.3');path.setAttribute('stroke-linejoin','round');path.setAttribute('stroke-linecap','round');
    svg.append(...ticks,path);holder.replaceChildren(svg);
    const selected=$('selected-detail');selected.replaceChildren(el('strong','','Relative time / observed fraud rates'),el('span','','The axis is relative day, not a calendar date.'));
  }
  function render(view){
    if(!state.data)return;
    state.view=views.includes(view)?view:'overview';
    const d=defineView(state.view),rows=normalizedRows(d.main,d.mainLabel,d.value),detail=normalizedRows(d.secondary,d.secondaryLabel,d.secondaryValue);
    document.querySelectorAll('[data-view]').forEach(a=>{
      const active=a.dataset.view===state.view;a.classList.toggle('active',active);
      if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
    });
    text('crumb-page',d.name.toUpperCase());text('hero-eyebrow',d.eyebrow);text('hero-title',d.title);text('hero-description',d.lede);
    text('aside-label','Highest observed '+(state.view==='features'?'feature importance':'segment signal'));
    text('aside-number',rows.length?d.form(rows[0].value):'—');
    text('aside-caption',rows.length?rows[0].label:'No segment rows reported for this view');
    text('source-title','GOVERNED REPORTING / '+String(state.data.meta?.backend||'source').toUpperCase());
    text('source-context','Dataset: '+String(state.data.meta?.dataset||'not reported')+' · source built: '+String(state.data.meta?.refreshed_at||'timestamp unavailable'));
    renderMetrics(d.metrics);text('brief-chart-heading',d.chartTitle);text('brief-chart-desc','Actual observed values. Longest mark represents the largest displayed metric.');
    text('takeaway',d.insight);text('scope-note',d.boundary);
    text('detail-title',d.detailTitle);text('detail-note','Independent observed metric, not an invented composite index.');
    makeBars($('brief-chart'),rows,d.form,'Observed in reporting snapshot');
    if(state.view==='trend')renderLine(get('daily_drift').map(r=>({label:String(r.transaction_day),value:r.fraud_rate})));
    makeBars($('detail-chart'),detail,d.secondaryForm,'Source metric');
    $('selected-detail').replaceChildren(el('strong','','Investigate a segment'),el('span','','Select any ranked mark to inspect its observed value.'));
    const protocol=$('protocol');protocol.replaceChildren(...[
      ['Source backend',String(state.data.meta?.backend||'not reported'),'No live data claims unless source metadata reports them'],
      ['Reporting dataset',String(state.data.meta?.dataset||'not reported'),'API returns governed source aggregates'],
      ['Updated at',String(state.data.meta?.refreshed_at||'not reported'),'Check freshness before operational decisions']
    ].map(([l,v,note])=>{const e=el('div','compare-band');e.append(el('strong','',l),el('span','',v),el('small','',note));return e;}));
    renderTable(detail,d.secondaryForm);text('table-title','Reported segment evidence');
    const governance=[
      d.boundary,
      'This is an exploratory presentation of aggregated labeled transaction data, not autonomous enforcement.',
      'Model scores and proxy variables are statistical signals, not proof of customer intent.',
      'Changes to operational policy require validation, calibration, coverage monitoring and authorized review.'
    ];
    $('limitations').replaceChildren(...governance.map(s=>el('li','',s)));
    setTab('brief');
  }
  document.querySelectorAll('[data-view]').forEach(link=>link.addEventListener('click',event=>{
    if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    event.preventDefault();
    history.pushState({},'',link.getAttribute('href'));
    render(link.dataset.view);
  }));
  document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>setTab(button.dataset.tab)));
  document.querySelector('.tabs').addEventListener('keydown',event=>{
    const tabs=[...document.querySelectorAll('[data-tab]')],index=tabs.indexOf(event.target);
    if(index<0||!['ArrowRight','ArrowLeft','Home','End'].includes(event.key))return;
    event.preventDefault();
    const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:
      (index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
    setTab(tabs[next].dataset.tab);tabs[next].focus();
  });
  setTab('brief');
  window.addEventListener('popstate',()=>render(new URLSearchParams(location.search).get('view')||'overview'));
  async function loadHistoricalCases(){
    const list=$('historical-review-queue'),detail=$('historical-review-detail');
    if(!list||!detail)return;
    const scope='Historical masked IEEE-CIS evaluation sample; scores are uncalibrated ranking outputs. No individual action or case status is recorded.';
    try {
      const response=await fetch('/api/enterprise/cases?limit=40',{headers:{Accept:'application/json'}});
      if(!response.ok)throw new Error('No committed historical case sample');
      const payload=await response.json();
      const rows=Array.isArray(payload.cases)
        ? payload.cases.filter(item=>item && Number.isSafeInteger(Number(item.transaction_id))).slice(0,40)
        : [];
      if(!rows.length){
        list.replaceChildren(el('p','','No historical review records are available.'));
        detail.textContent=scope;
        return;
      }
      function selectCase(item,button) {
        list.querySelectorAll('button').forEach(node=>node.setAttribute('aria-pressed',node===button?'true':'false'));
        const title=el('h3','','Historical transaction '+String(item.transaction_id));
        const description=el('p','studio-review-scope',scope);
        const dl=el('dl');
        const score=Number(item.model_probability);
        const displayScore=item.model_probability!==null && item.model_probability!==undefined &&
          Number.isFinite(score) && score>=0 && score<=1 ? score.toFixed(4) : 'Not available';
        const attrs=[
          ['Risk band',item.risk_band||'Unknown'],
          ['Uncalibrated model score',displayScore],
          ['Masked product group',item.product_cd||'Unknown'],
          ['Amount band',item.amount_band||'Unknown'],
          ['Identity coverage',item.identity_status||'Not reported'],
          ['Relative TransactionDT day',item.transaction_day??'Not reported']
        ];
        attrs.forEach(([label,value])=>{
          const wrapper=el('div');
          wrapper.append(el('dt','',label),el('dd','',String(value)));
          dl.append(wrapper);
        });
        detail.replaceChildren(title,dl,description);
      }
      const buttons=rows.map((item,i)=>{
        const button=el('button','studio-review-item');
        button.type='button';
        button.setAttribute('aria-pressed','false');
        button.setAttribute('aria-label','Inspect historical transaction '+String(item.transaction_id));
        button.append(el('span','','#'+String(item.transaction_id)),el('small','',String(item.risk_band||'Unscored')));
        button.addEventListener('click',()=>selectCase(item,button));
        if(i===0)button.dataset.firstCase='true';
        return button;
      });
      list.replaceChildren(...buttons);
      selectCase(rows[0],buttons[0]);
    } catch {
      list.replaceChildren(el('p','','Historical case sample unavailable. No warehouse fallback or simulated cases.'));
      detail.textContent=scope;
    }
  }

  fetch('/api/evidence-status',{headers:{Accept:'application/json'}})
    .then(res=>res.ok?res.json():null)
    .then(evidence=>{
      const target=$('studio-evidence-source');
      if(!target)return;
      if(evidence && typeof evidence.source_as_of==='string' && Number.isFinite(Date.parse(evidence.source_as_of))
          && evidence.source_status?.startsWith('historical_')){
        const day=new Date(evidence.source_as_of).toLocaleDateString('en-US',{timeZone:'UTC',year:'numeric',month:'short',day:'numeric'});
        target.textContent='Historical IEEE-CIS reporting built '+day+' UTC · '+evidence.age_days+
          ' days old · BigQuery parity unverified · Uncalibrated model ranking, not a live probability.';
      } else {
        target.textContent='Snapshot provenance could not be verified. Do not infer current data or live monitoring.';
      }
    })
    .catch(()=>{text('studio-evidence-source','Source verification unavailable. Historical scope; no live feed.');});
  let loading=false;
  async function loadDashboard(){
    if(loading)return;
    loading=true;$('main-content').setAttribute('aria-busy','true');
    $('studio-retry').hidden=true;
    text('status','Loading historical reporting evidence.');
    try{
      const res=await fetch('/api/dashboard',{headers:{Accept:'application/json'}});
      if(!res.ok)throw new Error('Dashboard data unavailable: HTTP '+res.status);
      const data=await res.json();
      if(!data||typeof data!=='object'||Array.isArray(data)||!Array.isArray(data.executive_kpis)||!data.executive_kpis.length)
        throw new Error('Reporting snapshot is incomplete.');
      state.data=data;render(new URLSearchParams(location.search).get('view')||'overview');
      text('status','Historical reporting evidence loaded.');
      loadHistoricalCases();
    }catch(error){
      $('status').replaceChildren(el('div','error',error.message+' Retry the connection to reload the committed snapshot.'));
      text('hero-title','Reporting evidence temporarily unavailable');
      document.querySelectorAll('.workspace-section').forEach(x=>x.hidden=true);
      $('studio-retry').hidden=false;
    }finally{
      loading=false;$('main-content').setAttribute('aria-busy','false');
    }
  }
  $('studio-retry').addEventListener('click',()=>loadDashboard());
  loadDashboard();
})();
