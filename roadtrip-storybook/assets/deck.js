'use strict';
gsap.registerPlugin(MotionPathPlugin);
const trip = JSON.parse(document.getElementById('trip-data').textContent);
const pages = trip.pages;
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const lines = value => esc(value).replace(/\n/g, '<br>');
const statuses = {confirmed:'已确认',booked:'已预订',planned:'计划',pending:'待确认',reference:'参考'};
const key = `roadtrip-storybook:${trip.id}:`;
let current = -1, routeTimeline = null, entranceTimeline = null, choiceIndex = 0;
let checks = {}, motionSetting = null, reduceMotion = false;
const preference = matchMedia('(prefers-reduced-motion: reduce)');
try {
  const saved = JSON.parse(localStorage.getItem(key + 'checks') || '{}');
  if (saved && typeof saved === 'object' && !Array.isArray(saved)) checks = saved;
  motionSetting = localStorage.getItem(key + 'motion');
} catch {}

function sections(items = []) {
  return `<ol class="timeline">${items.map(item => `<li>${item.time ? `<time>${esc(item.time)}</time>` : ''}<strong>${esc(item.title)}</strong>${item.status ? `<span class="status-tag status-${item.status}">${statuses[item.status]}</span>` : ''}${item.body ? `<p>${lines(item.body)}</p>` : ''}</li>`).join('')}</ol>`;
}
function companion(item) {
  const icon = item.icon || 'person';
  if (['bichon','poodle','dachshund','corgi','dog'].includes(icon)) return dog(icon === 'dog' ? 'bichon' : icon);
  if (icon === 'bag') return `<svg viewBox="0 0 100 100" aria-hidden="true">${art('bag',50,48,.85)}</svg>`;
  return '<svg viewBox="0 0 80 68" aria-hidden="true"><g stroke="#263c32" stroke-width="2.5" fill="#e9bc55"><circle cx="40" cy="18" r="12"/><path d="M19 60V47q0-20 21-20t21 20v13Z"/></g></svg>';
}
function body(page) {
  let html = '';
  if (page.metrics?.length) html += `<div class="metrics">${page.metrics.map(m => `<div class="metric"><strong>${esc(m.value)}</strong><b>${esc(m.unit)}</b><span>${esc(m.label)}</span></div>`).join('')}</div>`;
  if (page.companions?.length) html += `<div class="dog-roster">${page.companions.map(c => `<div class="dog-person">${companion(c)}<span>${esc(c.label)}</span></div>`).join('')}</div>`;
  if (page.sections?.length) html += `<div class="section-block">${sections(page.sections)}</div>`;
  if (page.choices?.length) html += `<div class="choice-buttons" aria-label="备选方案">${page.choices.map((c,i) => `<button data-choice="${i}" aria-pressed="${i===choiceIndex}">${esc(c.label)}</button>`).join('')}</div><div id="choice-content"></div><p class="mini-source">切换仅用于比较，不代表已确定安排。</p>`;
  if (page.table) html += `<div class="table-scroll"><table class="food-table"><thead><tr>${page.table.headers.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${page.table.rows.map(row => `<tr>${row.map(c => `<td>${lines(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  if (page.checklist?.length) html += `<div class="checklist">${page.checklist.map(c => `<label><input type="checkbox" data-check="${c.id}"${checks[page.id + ':' + c.id]===true?' checked':''}><span>${esc(c.label)}</span></label>`).join('')}</div><div class="checklist-progress"><span id="checklist-count"></span><button id="check-reset">重置本页清单</button></div>`;
  if (page.note) html += `<div class="note-strip${page.warning?' warn':''}">${lines(page.note)}</div>`;
  if (page.cover && current < pages.length-1) html += '<button class="cta" id="start-trip">翻开这段旅程 <span>→</span></button>';
  return html;
}

const positions = {
  1:[[360,320]], 2:[[155,220],[555,430]],
  3:[[155,170],[555,300],[290,490]],
  4:[[155,170],[555,170],[555,470],[155,470]],
  5:[[145,165],[385,155],[565,335],[360,490],[140,425]],
  6:[[140,165],[360,165],[575,165],[575,475],[360,475],[140,475]],
  7:[[135,150],[360,150],[585,150],[585,330],[585,500],[360,500],[135,500]],
  8:[[135,150],[360,150],[585,150],[585,330],[585,500],[360,500],[135,500],[135,330]]
};
function roadPath(a,b) {
  const dx=b.x-a.x,dy=b.y-a.y;
  return Math.abs(dx)>Math.abs(dy)
    ? `M${a.x} ${a.y}C${a.x+dx*.45} ${a.y+dy*.05-22} ${b.x-dx*.45} ${b.y-dy*.05+22} ${b.x} ${b.y}`
    : `M${a.x} ${a.y}C${a.x+dx*.1+35} ${a.y+dy*.45} ${b.x-dx*.1-35} ${b.y-dy*.45} ${b.x} ${b.y}`;
}
function marker(mode) {
  if (mode==='walk') return walker;
  if (mode==='cable') return gondola;
  if (mode==='train') return '<g class="doodle"><rect x="-28" y="-20" width="56" height="40" rx="8" fill="#a6b68a"/><path d="M-20-12h15V2h-15Zm25 0V-12h15V2Z" fill="#f6f1e5"/><path d="M-21 25h42M-17 20l-9 12m43-12 9 12"/></g>';
  if (mode==='boat') return '<g class="doodle"><path d="M-32 6h65L17 24h-35Z" fill="#cf5834"/><path d="M-5 4V-31L23 0H-5" fill="#e9bc55"/><path d="M-39 30q10-8 20 0t20 0 20 0 20 0"/></g>';
  return car;
}
function activeMap() {
  const page=pages[current]; return page.choices?.[choiceIndex]?.map || page.map;
}
function drawMap() {
  routeTimeline?.kill();
  const map=activeMap(), page=pages[current];
  const nodes=map.nodes.map((n,i)=>({...n,x:n.x ?? positions[map.nodes.length][i][0],y:n.y ?? positions[map.nodes.length][i][1]}));
  const byId=Object.fromEntries(nodes.map(n=>[n.id,n]));
  const legs=(map.legs||[]).map(l=>({...l,d:roadPath(byId[l.from],byId[l.to])}));
  const moving=legs.filter(l=>!l.optional), seen=new Set();
  let routes='';
  for (const leg of legs) {
    const pair=[leg.from,leg.to].sort().join(':'); if(seen.has(pair))continue;seen.add(pair);
    routes+=`<g opacity="${leg.optional?.35:1}"><path class="road-border" d="${leg.d}"/><path class="road-paper" d="${leg.d}"/><path class="road-grid" d="${leg.d}"/></g>`;
  }
  const stations=nodes.map((n,i)=>`<g class="node-group" id="stop-${n.id}"${n.page?` data-target="${n.page}" role="button" tabindex="0" aria-label="查看${esc(n.label)}"`:''}>${n.icon?art(n.icon,n.x,n.y-61,.73):''}<circle class="stop-dot" cx="${n.x}" cy="${n.y}" r="18"/><text class="node-number" text-anchor="middle" x="${n.x}" y="${n.y+5}">${i+1}</text><text class="map-label" text-anchor="middle" x="${n.x+(n.dx||0)}" y="${n.y+(n.dy??45)}">${esc(n.label)}</text>${n.detail?`<text class="map-sub" text-anchor="middle" x="${n.x+(n.dx||0)}" y="${n.y+(n.dy??45)+20}">${esc(n.detail)}</text>`:''}</g>`).join('');
  $('#map-kicker').textContent=map.title||page.name;
  $('#map-canvas').innerHTML=`<svg class="board" viewBox="0 0 720 640" aria-label="${esc(map.title||page.name)}。${esc(nodes.map(n=>n.label).join('，'))}。路线与比例为示意。"><title>${esc(map.title||page.name)}</title><desc>行程示意图，不是导航地图。</desc>${scenery()}${routes}${moving.map((l,i)=>`<path id="drive-path-${i}" class="active-route" d="${l.d}"/>`).join('')}${stations}<g id="vehicle" style="visibility:${moving.length?'visible':'hidden'}">${marker(moving[0]?.mode)}</g></svg>`;
  const finish=map.finish||'路线与方位为示意 · 按实际行程和导航执行';
  $('#route-status').textContent=finish;
  $('#route-replay').disabled=!moving.length;
  $('#route-pause').disabled=!moving.length||reduceMotion;
  $('#route-replay').textContent=reduceMotion?'查看路线':'↻ 走一遍';
  $('#route-pause').textContent='Ⅱ';$('#route-pause').setAttribute('aria-label','暂停路线动画');
  $$('[data-target]').forEach(n=>{
    const jump=()=>go(pages.findIndex(p=>p.id===n.dataset.target));
    n.addEventListener('click',jump);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();jump();}});
  });
  if(!moving.length){routeTimeline=null;return;}
  const vehicle=$('#vehicle');
  function complete(){ $('#route-status').textContent=finish;$('#route-pause').disabled=true; }
  if(reduceMotion){
    for(const leg of moving){$(`#stop-${leg.from}`).classList.add('is-reached');$(`#stop-${leg.to}`).classList.add('is-reached');}
    const last=moving[moving.length-1],path=$(`#drive-path-${moving.length-1}`);
    vehicle.innerHTML=marker(last.mode);
    gsap.set(vehicle,{motionPath:{path,align:path,alignOrigin:[.5,.5],autoRotate:(last.mode||'car')==='car',start:1,end:1}});
    routeTimeline=null;complete();return;
  }
  routeTimeline=gsap.timeline({paused:true,onComplete:complete});
  moving.forEach((leg,i)=>{
    const path=$(`#drive-path-${i}`),length=path.getTotalLength(),duration=Math.min(2.2,Math.max(1.15,length/170));
    gsap.set(path,{strokeDasharray:length,strokeDashoffset:length});
    routeTimeline.call(()=>{vehicle.innerHTML=marker(leg.mode);vehicle.dataset.mode=leg.mode||'car';$('#route-status').textContent=leg.label||`${byId[leg.from].label} → ${byId[leg.to].label}`;$(`#stop-${leg.from}`).classList.add('is-reached');});
    const at=routeTimeline.duration();
    routeTimeline.to(path,{strokeDashoffset:0,duration,ease:'power1.inOut'},at);
    routeTimeline.to(vehicle,{duration,rotation:0,motionPath:{path,align:path,alignOrigin:[.5,.5],autoRotate:(leg.mode||'car')==='car'},ease:'power1.inOut'},at);
    routeTimeline.call(()=>$(`#stop-${leg.to}`).classList.add('is-reached'));
    routeTimeline.to({},{duration:.22});
  });
  routeTimeline.play(0);
}

function renderChoice(){
  const choice=pages[current].choices?.[choiceIndex];if(!choice)return;
  $('#choice-content').innerHTML=sections(choice.sections)+(choice.note?`<div class="note-strip">${lines(choice.note)}</div>`:'');
}
function countChecks(){
  const page=pages[current];
  if(!page.checklist?.length)return;
  $('#checklist-count').textContent=`已勾选 ${page.checklist.filter(c=>checks[page.id+':'+c.id]===true).length} / ${page.checklist.length} 项 · 仅本机保存`;
}
function saveChecks(){
  try{localStorage.setItem(key+'checks',JSON.stringify(checks));}catch{$('#checklist-count').textContent+=' · 本次无法保存';}
}
function bindBody(){
  $('#start-trip')?.addEventListener('click',()=>go(current+1));
  $$('[data-choice]').forEach(b=>b.addEventListener('click',()=>{choiceIndex=+b.dataset.choice;$$('[data-choice]').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));renderChoice();drawMap();}));
  renderChoice();countChecks();
  $$('[data-check]').forEach(input=>input.addEventListener('change',()=>{checks[pages[current].id+':'+input.dataset.check]=input.checked;countChecks();saveChecks();}));
  $('#check-reset')?.addEventListener('click',()=>{for(const c of pages[current].checklist)delete checks[pages[current].id+':'+c.id];$$('[data-check]').forEach(c=>c.checked=false);countChecks();saveChecks();});
}
function go(index,{scroll=true}={}){
  index=Math.max(0,Math.min(pages.length-1,index));if(index===current)return;
  entranceTimeline?.kill();current=index;choiceIndex=0;
  const page=pages[current],titles=Array.isArray(page.title)?page.title:[page.title];
  $('#story').className='story'+(page.cover?' cover':'');
  $('#story').innerHTML=`<p class="eyebrow">${esc(page.eyebrow||page.chapter||'TRAVEL NOTES')}</p><h1 class="slide-title" id="slide-title" tabindex="-1">${titles.map((t,i)=>i===page.accent_line?`<span class="accent">${esc(t)}</span>`:esc(t)).join('<br>')}</h1>${page.lead?`<p class="lede">${lines(page.lead)}</p>`:''}<div class="story-content">${body(page)}</div><p class="story-note">${lines(page.foot)}</p>`;
  $('#story').scrollTop=0;
  $('#current-page').textContent=String(current+1).padStart(2,'0');$('#total-pages').textContent='/ '+pages.length;
  $('#chapter-name').textContent=page.chapter||page.name;$('.map-edition').textContent=`ROAD BOOK / ${String(current+1).padStart(2,'0')}`;
  $('#prev').disabled=current===0;$('#next').disabled=current===pages.length-1;
  gsap.set('#book-progress',{scaleX:(current+1)/pages.length});
  $$('[data-page]').forEach(b=>b.setAttribute('aria-current',String(+b.dataset.page===current)));
  $$('[data-chapter]').forEach(b=>b.setAttribute('aria-current',String(current>=+b.dataset.chapter&&current<+b.dataset.end)));
  document.title=`${current+1} / ${pages.length} · ${page.name} · ${trip.title}`;
  history.replaceState(null,'',`#${current+1}`);bindBody();drawMap();
  if(!reduceMotion)entranceTimeline=gsap.timeline().fromTo('#story > *',{y:12,autoAlpha:0},{y:0,autoAlpha:1,duration:.4,stagger:.05,clearProps:'transform,opacity,visibility'});
  if(scroll&&innerWidth<=780)window.scrollTo(0,0);
}
function setMotion(){
  reduceMotion=motionSetting==='off'||(motionSetting!=='on'&&preference.matches);
  $('#motion-toggle').setAttribute('aria-pressed',String(!reduceMotion));
  $('#motion-toggle').setAttribute('aria-label',reduceMotion?'开启动效':'关闭动效');$('#motion-toggle span').textContent=reduceMotion?'关':'开';
}
$('#motion-toggle').addEventListener('click',()=>{motionSetting=reduceMotion?'on':'off';try{localStorage.setItem(key+'motion',motionSetting);}catch{}setMotion();entranceTimeline?.progress(1);drawMap();});
preference.addEventListener('change',()=>{setMotion();entranceTimeline?.progress(1);drawMap();});
$('#prev').addEventListener('click',()=>go(current-1));$('#next').addEventListener('click',()=>go(current+1));
$('#route-replay').addEventListener('click',drawMap);
$('#route-pause').addEventListener('click',()=>{if(!routeTimeline)return;const paused=routeTimeline.paused();routeTimeline.paused(!paused);$('#route-pause').textContent=paused?'Ⅱ':'▶';$('#route-pause').setAttribute('aria-label',paused?'暂停路线动画':'继续路线动画');});
const chapters=[];
pages.forEach((p,i)=>{const name=p.chapter||p.name;if(chapters.length&&chapters[chapters.length-1].name===name)chapters[chapters.length-1].end=i+1;else chapters.push({name,start:i,end:i+1});});
$('#chapter-nav').innerHTML=chapters.map(c=>`<button data-chapter="${c.start}" data-end="${c.end}">${esc(c.name)}</button>`).join('');
$$('[data-chapter]').forEach(b=>b.addEventListener('click',()=>go(+b.dataset.chapter)));
$('#contents-list').innerHTML=pages.map((p,i)=>`<button data-page="${i}"><span>${String(i+1).padStart(2,'0')}</span>${esc(p.name)}</button>`).join('');
let dialogTimeline=null;
function openDialog(selector){dialogTimeline=routeTimeline&&!routeTimeline.paused()&&routeTimeline.progress()<1?routeTimeline:null;dialogTimeline?.pause();const d=$(selector);d.showModal();if(!reduceMotion)gsap.fromTo(d,{y:25,autoAlpha:0},{y:0,autoAlpha:1,duration:.25,clearProps:'transform,opacity,visibility'});}
$('#contents-open').addEventListener('click',()=>openDialog('#contents-dialog'));$('#source-open').addEventListener('click',()=>openDialog('#source-dialog'));
$$('dialog').forEach(d=>{d.addEventListener('close',()=>{dialogTimeline?.play();dialogTimeline=null;});$('.dialog-close',d).addEventListener('click',()=>d.close());d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});});
$$('[data-page]').forEach(b=>b.addEventListener('click',()=>{$('#contents-dialog').close();go(+b.dataset.page);$('#slide-title').focus({preventScroll:true});}));
window.addEventListener('keydown',e=>{if($('dialog[open]')||e.altKey||e.ctrlKey||e.metaKey||e.target.matches('input,textarea,select,[contenteditable=true]'))return;if(['ArrowRight','PageDown'].includes(e.key)){e.preventDefault();go(current+1);}else if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(current-1);}else if(e.key==='Home'){e.preventDefault();go(0);}else if(e.key==='End'){e.preventDefault();go(pages.length-1);}else if(e.key===' '&&!e.target.closest('button,a,[role=button]')){e.preventDefault();go(current+1);}});
let touchStart=null;
$('#stage').addEventListener('touchstart',e=>{touchStart=null;if(e.target.closest('button,a,input,label,[role=button]'))return;touchStart={x:e.changedTouches[0].clientX,y:e.changedTouches[0].clientY};},{passive:true});
$('#stage').addEventListener('touchend',e=>{if(!touchStart)return;const dx=e.changedTouches[0].clientX-touchStart.x,dy=e.changedTouches[0].clientY-touchStart.y;if(Math.abs(dx)>75&&Math.abs(dx)>Math.abs(dy)*1.6)go(current+(dx<0?1:-1));touchStart=null;},{passive:true});
window.addEventListener('hashchange',()=>{const index=parseInt(location.hash.slice(1),10);if(Number.isInteger(index))go(index-1);});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&routeTimeline&&routeTimeline.progress()<1){routeTimeline.pause();$('#route-pause').textContent='▶';$('#route-pause').setAttribute('aria-label','继续路线动画');}});
setMotion();const initial=parseInt(location.hash.slice(1),10);go(Number.isInteger(initial)?initial-1:0,{scroll:false});
