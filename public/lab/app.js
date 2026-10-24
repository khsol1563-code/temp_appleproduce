const state = { data: null, city: "영주", metric: "연평균기온", start: 2012, end: 2025, trend: true, agri: "재배면적", mapYear: 2025, charts: {}, map: null, markers: null, boundary: null, solution: "" };
const colors = { 영주: "#c7352e", 문경: "#287455", 영천: "#2f7fb5" };
const metricKeys = { 연평균기온: "연평균기온", 평균최저기온: "평균최저기온", 평균최고기온: "평균최고기온" };
const agriConfig = {
  재배면적: { key: "재배면적_ha", label: "경북 사과 재배면적", unit: "ha", color: "rgba(126, 197, 197, .72)", type: "bar" },
  총생산량: { key: "총생산량_톤", label: "경북 사과 총생산량", unit: "톤", color: "#2a9d8f", type: "line" },
  "10a당 생산량": { key: "10a당생산량_kg", label: "경북 사과 10a당 생산량", unit: "kg", color: "#6a994e", type: "line" }
};

const fmt = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 1 });
const intFmt = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 0 });
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function parseCsv(text) {
  const rows=[]; let row=[], cell="", quoted=false;
  for (let i=0;i<text.length;i++) { const c=text[i], next=text[i+1];
    if (c==='"' && quoted && next==='"') { cell+='"'; i++; }
    else if (c==='"') quoted=!quoted;
    else if (c===',' && !quoted) { row.push(cell.trim()); cell=""; }
    else if ((c==='\n' || c==='\r') && !quoted) { if(c==='\r'&&next==='\n') i++; row.push(cell.trim()); if(row.some(Boolean)) rows.push(row); row=[]; cell=""; }
    else cell+=c;
  }
  row.push(cell.trim()); if(row.some(Boolean)) rows.push(row);
  const [header,...body]=rows; if(!header) throw new Error('CSV에 제목 행이 없습니다.');
  const key=Object.fromEntries(header.map((name,i)=>[name.replace(/^\uFEFF/,''),i]));
  const value=(r,name)=>r[key[name]]?.trim() ?? '';
  if (!['구분','지역','연도'].every(name=>name in key)) throw new Error('구분, 지역, 연도 열이 필요합니다.');
  const cities={}, apple=[];
  body.forEach(r=>{ const type=value(r,'구분'), year=Number(value(r,'연도')); if(!Number.isFinite(year)) return;
    if(type==='기온') { const city=value(r,'지역'); const record={연도:year,연평균기온:Number(value(r,'연평균기온')),평균최저기온:Number(value(r,'평균최저기온')),평균최고기온:Number(value(r,'평균최고기온'))};
      if(city && Object.values(record).every(Number.isFinite)) (cities[city]??=[]).push(record);
    } else if(type==='사과') { const record={연도:year,재배면적_ha:Number(value(r,'재배면적_ha')),총생산량_톤:Number(value(r,'총생산량_톤')),'10a당생산량_kg':Number(value(r,'10a당생산량_kg'))}; if(Object.values(record).every(Number.isFinite)) apple.push(record); }
  });
  if(Object.keys(cities).length<1 || apple.length<2) throw new Error('기온 행 1개 이상과 사과 행 2개 이상이 필요합니다.');
  const fallbackCoords={영주:{lat:36.8057,lon:128.6241,note:'대표 위치'},문경:{lat:36.5867,lon:128.1868,note:'대표 위치'},영천:{lat:35.9732,lon:128.9386,note:'대표 위치'}};
  return {cities:Object.fromEntries(Object.entries(cities).map(([name,records])=>[name,{records:records.sort((a,b)=>a.연도-b.연도),coords:fallbackCoords[name]??fallbackCoords.영주}])),apple:{records:apple.sort((a,b)=>a.연도-b.연도)}};
}

async function loadCsv(file) {
  try { const data=parseCsv(await file.text()); const years=data.apple.records.map(r=>r.연도), min=Math.min(...years), max=Math.max(...years); state.data=data; state.city=Object.keys(data.cities)[0]; state.start=min; state.end=max; state.mapYear=max;
    ['start-year','end-year','map-year'].forEach(id=>{const input=$('#'+id); input.min=min; input.max=max; input.value=id==='start-year'?min:max;}); $('#start-year-output').textContent=min; $('#end-year-output').textContent=max; $('#csv-status').textContent=`${file.name}을(를) 이 브라우저에서만 반영했습니다. 서버 전송이나 AI 호출은 없습니다.`; renderDataViews(); renderMap();
  } catch(error) { $('#csv-status').textContent=`CSV를 읽지 못했습니다: ${error.message}`; }
}

function filteredCity(city = state.city) {
  return state.data.cities[city].records.filter(row => row.연도 >= state.start && row.연도 <= state.end);
}
function filteredApple() { return state.data.apple.records.filter(row => row.연도 >= state.start && row.연도 <= state.end); }
function pct(start, end) { return (end / start - 1) * 100; }
function correlation(xs, ys) {
  const mx = xs.reduce((a,b)=>a+b,0)/xs.length, my = ys.reduce((a,b)=>a+b,0)/ys.length;
  let top=0, left=0, right=0;
  xs.forEach((x,i)=>{ const dx=x-mx, dy=ys[i]-my; top+=dx*dy; left+=dx*dx; right+=dy*dy; });
  return top / Math.sqrt(left * right);
}
function regression(xs, ys) {
  const mx=xs.reduce((a,b)=>a+b,0)/xs.length, my=ys.reduce((a,b)=>a+b,0)/ys.length;
  let top=0,bottom=0; xs.forEach((x,i)=>{top+=(x-mx)*(ys[i]-my);bottom+=(x-mx)**2;});
  const slope=top/bottom, intercept=my-slope*mx; return {slope,intercept};
}
function corrLabel(value) {
  const n=Math.abs(value); const strength=n<.2?"거의 뚜렷하지 않은":n<.4?"약한":n<.7?"중간 정도의":"강한";
  return `${strength} ${value<0?"음의":"양의"} 상관 경향`;
}
function chartBase(title="") {
  return { responsive:true, maintainAspectRatio:false, interaction:{mode:"index",intersect:false}, plugins:{legend:{position:"bottom",labels:{usePointStyle:true,padding:18,font:{family:"Noto Sans KR",weight:"600"}}},tooltip:{backgroundColor:"rgba(20,34,27,.94)",padding:12,titleFont:{family:"Noto Sans KR"},bodyFont:{family:"Noto Sans KR"}},title:{display:!!title,text:title}}, scales:{x:{grid:{display:false},ticks:{font:{family:"Noto Sans KR"}}},y:{grid:{color:"rgba(70,90,78,.12)"},ticks:{font:{family:"Noto Sans KR"}}}} };
}
function replaceChart(id, config) {
  if (state.charts[id]) state.charts[id].destroy();
  const canvas=document.getElementById(id); if (!canvas || !window.Chart) return;
  state.charts[id]=new Chart(canvas,config);
}
function metricCard(label,value,detail){return `<article class="metric-card"><span>${label}</span><strong>${value}</strong><small>${detail}</small></article>`;}

function renderClimate() {
  $$('[data-city]').forEach(button=>button.classList.toggle('active',button.dataset.city===state.city));
  const rows=filteredCity(); const first=rows[0], last=rows.at(-1); const change=last.연평균기온-first.연평균기온;
  const fit=regression(rows.map(r=>r.연도),rows.map(r=>r.연평균기온));
  const hottest=rows.reduce((a,b)=>a.연평균기온>b.연평균기온?a:b);
  $("#climate-metrics").innerHTML=[
    metricCard("처음 연평균기온",`${first.연평균기온.toFixed(1)}°C`,`${first.연도}년`),
    metricCard("마지막 연평균기온",`${last.연평균기온.toFixed(1)}°C`,`${change>=0?"+":""}${change.toFixed(1)}°C 변화`),
    metricCard("10년당 추세",`${fit.slope>=0?"+":""}${(fit.slope*10).toFixed(2)}°C`,`선형 추세`),
    metricCard("가장 더운 해",`${hottest.연도}년`,`${hottest.연평균기온.toFixed(1)}°C`)
  ].join("");
  $("#city-chart-title").textContent=`${state.city} ${state.metric} 변화`;
  $("#bundle-title").textContent=`${state.city} 연평균·최저·최고기온`;
  const labels=rows.map(r=>r.연도), values=rows.map(r=>r[metricKeys[state.metric]]);
  const fitMetric=regression(labels,values);
  const datasets=[{label:state.metric,data:values,borderColor:colors[state.city],backgroundColor:colors[state.city],pointRadius:5,pointHoverRadius:7,borderWidth:3,tension:.22}];
  if(state.trend) datasets.push({label:"선형 추세선",data:labels.map(x=>fitMetric.slope*x+fitMetric.intercept),borderColor:"#5f6963",pointRadius:0,borderDash:[7,6],borderWidth:2});
  const cityOptions=chartBase(); cityOptions.scales.y.title={display:true,text:"기온 (°C)"};
  replaceChart("city-chart",{type:"line",data:{labels,datasets},options:cityOptions});
  $("#city-caption").textContent=`${state.city}의 ${state.start}~${state.end}년 ${state.metric}을 표시했습니다. 시작과 끝의 연평균기온 차이는 ${change>=0?"+":""}${change.toFixed(1)}°C입니다.`;

  const allDatasets=Object.keys(state.data.cities).map(city=>({label:city,data:filteredCity(city).map(r=>r.연평균기온),borderColor:colors[city],backgroundColor:colors[city],pointStyle:city==="영주"?"circle":city==="문경"?"rect":"triangle",pointRadius:4,borderWidth:2.5,tension:.18}));
  replaceChart("all-city-chart",{type:"line",data:{labels,datasets:allDatasets},options:chartBase()});
  const changes=Object.entries(state.data.cities).map(([city,item])=>item.records.at(-1).연평균기온-item.records[0].연평균기온);
  const changeOptions=chartBase(); changeOptions.plugins.legend.display=false; changeOptions.scales.y.title={display:true,text:"변화량 (°C)"};
  replaceChart("change-chart",{type:"bar",data:{labels:Object.keys(state.data.cities),datasets:[{data:changes,backgroundColor:Object.keys(state.data.cities).map(c=>colors[c]),borderRadius:10,maxBarThickness:70}]},options:changeOptions});
  replaceChart("bundle-chart",{type:"line",data:{labels,datasets:[
    {label:"연평균기온",data:rows.map(r=>r.연평균기온),borderColor:"#e63946",backgroundColor:"#e63946",pointStyle:"circle",pointRadius:4,borderWidth:3},
    {label:"평균최저기온",data:rows.map(r=>r.평균최저기온),borderColor:"#457b9d",backgroundColor:"#457b9d",pointStyle:"rect",borderDash:[6,4],pointRadius:4,borderWidth:2},
    {label:"평균최고기온",data:rows.map(r=>r.평균최고기온),borderColor:"#f4a261",backgroundColor:"#f4a261",pointStyle:"triangle",borderDash:[6,4],pointRadius:4,borderWidth:2}
  ]},options:chartBase()});
  $("#climate-table tbody").innerHTML=rows.map(r=>`<tr><td>${r.연도}</td><td>${r.연평균기온.toFixed(1)}°C</td><td>${r.평균최저기온.toFixed(1)}°C</td><td>${r.평균최고기온.toFixed(1)}°C</td></tr>`).join("");
  $("#context-pill").textContent=`${state.city} · ${state.start}~${state.end}`;
}

function renderCompare() {
  const city=filteredCity(), apple=filteredApple(); const firstA=apple[0],lastA=apple.at(-1),firstC=city[0],lastC=city.at(-1);
  const corr=correlation(city.map(r=>r.연평균기온),apple.map(r=>r.총생산량_톤));
  $("#apple-metrics").innerHTML=[
    metricCard(`${state.city} 기온 변화`,`${(lastC.연평균기온-firstC.연평균기온)>=0?"+":""}${(lastC.연평균기온-firstC.연평균기온).toFixed(1)}°C`,`${state.start}→${state.end}`),
    metricCard("경북 재배면적 변화",`${pct(firstA.재배면적_ha,lastA.재배면적_ha).toFixed(1)}%`,`${intFmt.format(firstA.재배면적_ha)}→${intFmt.format(lastA.재배면적_ha)}ha`),
    metricCard("경북 총생산량 변화",`${pct(firstA.총생산량_톤,lastA.총생산량_톤).toFixed(1)}%`,`${intFmt.format(firstA.총생산량_톤)}→${intFmt.format(lastA.총생산량_톤)}톤`),
    metricCard("기온·총생산량 상관",corr.toFixed(2),corrLabel(corr))
  ].join("");
  const config=agriConfig[state.agri]; $("#dual-title").textContent=`${state.city} 기온과 ${config.label} 비교`;
  const options=chartBase(); options.scales.y={position:"left",title:{display:true,text:`${config.label} (${config.unit})`},ticks:{callback:v=>intFmt.format(v)},grid:{color:"rgba(70,90,78,.12)"}}; options.scales.y1={position:"right",title:{display:true,text:"연평균기온 (°C)"},grid:{drawOnChartArea:false}};
  replaceChart("dual-chart",{data:{labels:apple.map(r=>r.연도),datasets:[{type:config.type,label:`${config.label} (${config.unit})`,data:apple.map(r=>r[config.key]),backgroundColor:config.color,borderColor:config.color,borderWidth:config.type==="bar"?0:3,pointRadius:config.type==="bar"?0:4,borderRadius:8,yAxisID:"y"},{type:"line",label:`${state.city} 연평균기온 (°C)`,data:city.map(r=>r.연평균기온),borderColor:"#e63946",backgroundColor:"#e63946",borderDash:[7,5],pointRadius:5,borderWidth:3,yAxisID:"y1"}]},options});
  $("#scatter-title").textContent=`${state.city} 기온과 경북 사과 총생산량`;
  const x=city.map(r=>r.연평균기온), y=apple.map(r=>r.총생산량_톤), fit=regression(x,y), sorted=[...x].sort((a,b)=>a-b);
  const scatterOptions=chartBase(); scatterOptions.parsing=false; scatterOptions.scales.x={type:"linear",title:{display:true,text:"연평균기온 (°C)"},grid:{color:"rgba(70,90,78,.1)"}};scatterOptions.scales.y={title:{display:true,text:"경북 총생산량 (톤)"},ticks:{callback:v=>intFmt.format(v)}};
  replaceChart("scatter-chart",{type:"scatter",data:{datasets:[{label:"연도별 값",data:x.map((value,i)=>({x:value,y:y[i],year:apple[i].연도})),backgroundColor:colors[state.city],pointRadius:6},{label:"회귀 추세선",type:"line",data:sorted.map(value=>({x:value,y:fit.slope*value+fit.intercept})),borderColor:"#4b5650",borderDash:[6,5],pointRadius:0,borderWidth:2}]},options:scatterOptions});
  const corrValues=Object.keys(state.data.cities).map(name=>correlation(filteredCity(name).map(r=>r.연평균기온),apple.map(r=>r.총생산량_톤)));
  const corrOptions=chartBase(); corrOptions.indexAxis="y";corrOptions.plugins.legend.display=false;corrOptions.scales.x={min:-1,max:1,title:{display:true,text:"−1 ↔ +1"},grid:{color:"rgba(70,90,78,.12)"}};corrOptions.scales.y={grid:{display:false}};
  replaceChart("corr-chart",{type:"bar",data:{labels:Object.keys(state.data.cities),datasets:[{data:corrValues,backgroundColor:Object.keys(state.data.cities).map(c=>colors[c]),borderRadius:7}]},options:corrOptions});
  $("#corr-value").textContent=corr.toFixed(2); $("#corr-label").textContent=corrLabel(corr);
}

function tempColor(change){return change<0?"#4388c7":change<.7?"#e5bd45":change<1.5?"#eb8b3d":"#d34435";}
async function initMap() {
  if(!window.L){$("#map-fallback").style.display="block";return;}
  $("#map-fallback").style.display="none";
  state.map=L.map("map",{scrollWheelZoom:false,zoomControl:true,attributionControl:false}).setView([36.35,128.65],8);
  state.markers=L.layerGroup().addTo(state.map);
  try {
    const response=await fetch("data/gyeongbuk.geojson");
    if(!response.ok)throw new Error(`GeoJSON ${response.status}`);
    const geo=await response.json();
    state.boundary=L.geoJSON(geo,{style:{color:"#315f4a",weight:1.5,fillColor:"#b8d8bd",fillOpacity:.72}}).addTo(state.map);
    state.map.fitBounds(state.boundary.getBounds(),{padding:[24,24]});
  } catch(error){
    console.info("경계 GeoJSON을 불러오지 못해 내장 대체 지도를 사용합니다.",error);
    state.map.remove();state.map=null;state.markers=null;$("#map-fallback").style.display="block";
  }
  renderMap();
}
function renderMap() {
  $("#map-year-label").textContent=state.mapYear; $("#map-side-year").textContent=state.mapYear;
  if(state.markers)state.markers.clearLayers();
  const cards=[];
  Object.entries(state.data.cities).forEach(([city,item])=>{const row=item.records.find(r=>r.연도===state.mapYear),base=item.records[0],change=row.연평균기온-base.연평균기온,color=tempColor(change);cards.push(`<article class="map-city-card"><header><strong>${city}</strong><b>${row.연평균기온.toFixed(1)}°C</b></header><p>최저 ${row.평균최저기온.toFixed(1)}°C · 최고 ${row.평균최고기온.toFixed(1)}°C</p><small>2012년 대비 ${change>=0?"+":""}${change.toFixed(1)}°C</small></article>`);if(state.markers){const radius=Math.max(10,row.연평균기온*1.05);L.circleMarker([item.coords.lat,item.coords.lon],{radius,color:"#fff",weight:3,fillColor:color,fillOpacity:.9}).bindTooltip(`${city} ${row.연평균기온.toFixed(1)}°C`,{permanent:true,direction:"top",className:"city-tooltip"}).bindPopup(`<b>${city}</b><br>${state.mapYear}년 연평균 ${row.연평균기온.toFixed(1)}°C<br>평균최저 ${row.평균최저기온.toFixed(1)}°C<br>평균최고 ${row.평균최고기온.toFixed(1)}°C<br>2012년 대비 ${change>=0?"+":""}${change.toFixed(1)}°C<br><small>${item.coords.note}</small>`).addTo(state.markers);}});
  $("#map-city-cards").innerHTML=cards.join("");
}

function renderAll(){renderClimate();renderCompare();renderMap();}
function showSection(id){
  $$('.page-section').forEach(section=>section.classList.toggle('active',section.id===id));
  $$('.nav-btn').forEach(btn=>btn.classList.toggle('active',btn.dataset.target===id));
  window.scrollTo({top:0,behavior:'smooth'});
  if(id==='map-section'){
    if(!state.map)initMap();
    else setTimeout(()=>{state.map.invalidateSize();if(state.boundary)state.map.fitBounds(state.boundary.getBounds(),{padding:[24,24]});},120);
  }
}

function bindEvents(){
  $('#csv-upload')?.addEventListener('change',e=>{const file=e.target.files?.[0];if(file)loadCsv(file);});
  $$('.nav-btn').forEach(btn=>btn.addEventListener('click',()=>showSection(btn.dataset.target))); $$('[data-jump]').forEach(btn=>btn.addEventListener('click',()=>showSection(btn.dataset.jump)));
  $$('[data-city]').forEach(button=>button.addEventListener('click',()=>{state.city=button.dataset.city;renderAll();})); $('#metric-select').addEventListener('change',e=>{state.metric=e.target.value;renderClimate();});
  $('#start-year').addEventListener('input',e=>{state.start=Math.min(+e.target.value,state.end-1);e.target.value=state.start;$('#start-year-output').textContent=state.start;renderAll();});
  $('#end-year').addEventListener('input',e=>{state.end=Math.max(+e.target.value,state.start+1);e.target.value=state.end;$('#end-year-output').textContent=state.end;renderAll();});
  $('#trend-toggle').addEventListener('change',e=>{state.trend=e.target.checked;renderClimate();}); $('#table-toggle').addEventListener('change',e=>$('#climate-table-wrap').classList.toggle('hidden',!e.target.checked));
  $$('[data-agri]').forEach(btn=>btn.addEventListener('click',()=>{$$('[data-agri]').forEach(b=>b.classList.remove('active'));btn.classList.add('active');state.agri=btn.dataset.agri;renderCompare();}));
  $('#map-year').addEventListener('input',e=>{state.mapYear=+e.target.value;renderMap();});
  $$('.prediction').forEach(btn=>btn.addEventListener('click',()=>{$$('.prediction').forEach(b=>b.classList.remove('selected'));btn.classList.add('selected');localStorage.setItem('apple-prediction',btn.dataset.prediction);$('#prediction-feedback').textContent=`나의 예상: “${btn.dataset.prediction}”. 이제 그래프로 확인해 보세요.`;}));
  $('#check-answer').addEventListener('click',()=>{const chosen=$('input[name="quiz"]:checked');if(!chosen){$('#quiz-feedback').textContent='먼저 문장을 하나 골라 주세요.';return;}showQuizResult(chosen.value==='correct');});
  $$('.solution-options button').forEach(btn=>btn.addEventListener('click',()=>{$$('.solution-options button').forEach(b=>b.classList.remove('selected'));btn.classList.add('selected');state.solution=btn.textContent;}));
  $('#build-proposal').addEventListener('click',()=>{const reason=$('#solution-reason').value.trim();$('#proposal-output').textContent=!state.solution?'먼저 해결책을 하나 골라 주세요.':!reason?'그 해결책을 고른 이유를 적어 주세요.':`나의 제안: “${state.solution}”이 중요합니다. 그 이유는 ${reason}`;});
  $('#submit-proposal').addEventListener('click',submitProposal);
  renderProposalTable();
}

function playTone(correct){
  const AudioContext=window.AudioContext||window.webkitAudioContext;if(!AudioContext)return;
  const ctx=new AudioContext(),now=ctx.currentTime,notes=correct?[523.25,659.25,783.99,1046.5]:[180,120];
  notes.forEach((frequency,index)=>{const osc=ctx.createOscillator(),gain=ctx.createGain();osc.type=correct?'triangle':'square';osc.frequency.value=frequency;gain.gain.setValueAtTime(.0001,now+index*.14);gain.gain.exponentialRampToValueAtTime(correct?.16:.1,now+index*.14+.02);gain.gain.exponentialRampToValueAtTime(.0001,now+index*.14+.24);osc.connect(gain).connect(ctx.destination);osc.start(now+index*.14);osc.stop(now+index*.14+.26);});
}
function showQuizResult(correct){
  const overlay=$('#result-overlay'),symbol=$('#result-symbol'),message=$('#result-message'),field=$('#particle-field');
  symbol.textContent=correct?'O':'×';message.textContent=correct?'정답입니다!':'오답입니다. 다시 생각해보세요.';overlay.className=`result-overlay show ${correct?'correct':'wrong'}`;overlay.setAttribute('aria-hidden','false');field.innerHTML='';
  if(correct){for(let i=0;i<36;i++){const particle=document.createElement('i');particle.style.setProperty('--x',`${Math.random()*100}%`);particle.style.setProperty('--delay',`${Math.random()*.35}s`);particle.style.setProperty('--hue',`${Math.floor(Math.random()*360)}`);field.appendChild(particle);}}
  playTone(correct);$('#quiz-feedback').textContent='';
  setTimeout(()=>overlay.classList.add('fade-symbol'),2000);setTimeout(()=>{overlay.className='result-overlay';overlay.setAttribute('aria-hidden','true');field.innerHTML='';$$('input[name="quiz"]').forEach(input=>input.checked=false);},3000);
}
function proposalRows(){try{return JSON.parse(localStorage.getItem('apple-class-proposals')||'[]');}catch{return [];}}
function escapeHtml(value){return String(value).replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));}
function renderProposalTable(){const body=$('#proposal-table tbody');if(!body)return;const rows=proposalRows();body.innerHTML=rows.length?rows.map(row=>`<tr><td>${escapeHtml(row.name)}</td><td>${escapeHtml(row.solution)}</td><td>${escapeHtml(row.reason)}</td><td>${escapeHtml(row.createdAt)}</td></tr>`).join(''):'<tr><td colspan="4">아직 제출한 제안이 없습니다.</td></tr>';}
async function submitProposal(){
  const name=$('#student-name').value.trim(),reason=$('#solution-reason').value.trim();if(!name||!state.solution||!reason){$('#proposal-output').textContent='학생 이름, 해결책, 제안 근거를 모두 입력해 주세요.';return;}
  const payload={name,solution:state.solution,reason,observation:$('#observation').value.trim()};$('#submit-proposal').disabled=true;
  const row={...payload,createdAt:new Date().toLocaleString('ko-KR')};const rows=proposalRows();rows.unshift(row);localStorage.setItem('apple-class-proposals',JSON.stringify(rows.slice(0,20)));renderProposalTable();$('#proposal-output').textContent=`${name} 학생의 제안은 이 브라우저에만 저장되었습니다.`;$('#submit-proposal').disabled=false;
}

async function boot(){
  try{const response=await fetch('data/analysis.json');if(!response.ok)throw new Error(`데이터 응답 ${response.status}`);state.data=await response.json();Chart.defaults.font.family='Noto Sans KR';Chart.defaults.color='#526159';bindEvents();renderAll();const saved=localStorage.getItem('apple-prediction');if(saved){const button=$(`.prediction[data-prediction="${saved}"]`);if(button)button.click();}}
  catch(error){console.error(error);document.body.innerHTML=`<main class="fatal"><h1>데이터를 불러오지 못했습니다.</h1><p>${error.message}</p><p>로컬에서는 파일을 직접 열지 말고 웹 서버로 실행해 주세요.</p></main>`;}
}
boot();
