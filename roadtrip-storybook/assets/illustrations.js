// Original vector illustrations; no itinerary data.
const handIcons = {
  mountain:'<path d="M-55 24 -20-35 2 0 23-47 67 23Z" fill="#b6c49a"/><path d="m-34-10 14-25 15 24m13-12 15-24 16 27M-65 30l132-3"/><path d="m-17-28 5 20m34-25 9 24" stroke-width="1.3"/>',
  tree:'<path d="M0 29V-5m-18 18L0-23l20 35Zm-13-18L0-39 14-8Z" fill="#9fb784"/><path d="m-6 32 18-2"/>',
  house:'<path d="M-40-5h80v46h-80Z" fill="#f9f5e7"/><path d="m-49-4 20-28 31 8 26-6L49-4Z" fill="#65765f"/><path d="M-33-11h69M-36-5v46M-8 41V12h20v29M-26 8h11v13h-11Zm46 0h11v13H20Z"/><path d="M-48 45h97"/>',
  tower:'<path d="M-21 40V-48h42v88" fill="#f4dec0"/><path d="m-29-42 29-18 30 18Zm-34 29 33-16 35 16Zm-39 28 39-16 39 16Z" fill="#67785f"/><path d="M0-76v15M-42 41h84M-8 40V24h16v16M-3-35v10M-3-5v9"/>',
  fish:'<path d="M-43 0q35-39 73 0Q-8 33-43 0Z" fill="#db623e"/><path d="m30 0 27-23-1 43Z" fill="#e9ba53"/><path d="M-27-11q13 11 0 22m17-29q14 18 0 35M7-17q11 18 0 34M-4-22V-37m0 66v15"/><circle cx="-30" cy="-3" r="3" fill="#263c32"/><path d="m-13 41 9-12 10 12" stroke="#cb4d2b"/>',
  cup:'<path d="M-22-11h39l-3 35h-31Zm40 3q23-7 19 10-1 12-20 9M-31 29h65M-12-19q-8-9 0-19m16 17q-8-9 0-18" fill="#f9f5e7"/>',
  charge:'<path d="M-25-35h43v65h-43Z" fill="#a6b68a"/><path d="M-18-27h29v23h-29ZM18-15q20-2 20 14v20q0 9 9 9M-30 32h56"/><path d="m0-21-8 13h10L-4 7" stroke="#f6f1e5" stroke-width="4"/>',
  flag:'<path d="M-13 40V-38l50 8-50 22" fill="#e8b955"/><path d="M-26 41h30"/>',
  hotpot:'<path d="M-38 0h77q-1 33-39 31Q-35 31-38 0ZM-37 7h-13v12h16M39 7h12v12H35" fill="#e8b955"/><path d="M-24 36h49M-12-10q-12-10 0-21m19 22q-12-10 0-21m18 23q-12-10 0-21M-29 3q29 10 58 0"/>',
  bag:'<path d="M-31-23h62v63h-62Zm18 0v-14h26v14M-16-18v53M16-18v53" fill="#e7b754"/><path d="M-25 40v8m48-8v8"/>',
  sun:'<circle r="18" fill="#e9bc55"/><path d="M0-36v10M0 26v10M-36 0h10M26 0h10M-26-26l8 8M18 18l8 8M-26 26l8-8M18-18l8-8"/>',
};
function art(type,x,y,scale=1,rotation=0){return `<g class="doodle" transform="translate(${x} ${y}) rotate(${rotation}) scale(${scale})">${handIcons[type]||''}</g>`;}
function dog(kind){
  const coats={bichon:['#fffdf1','#fffdf1'],poodle:['#4a443c','#3c3730'],dachshund:['#b07a47','#684c35'],corgi:['#d19a59','#fff3d9']};
  const [coat,ear]=coats[kind];
  let ears=kind==='corgi'?'<path d="m18 26-4-21 20 15m12 0L66 5l-4 25" fill="'+coat+'"/>':kind==='dachshund'?'<path d="M22 19Q3 9 9 48q11 13 19-13m25-16q19-10 17 26-9 16-17-10" fill="'+ear+'"/>':'<path d="M22 17Q6 8 8 27T24 39m31-22q19-9 17 12T54 39" fill="'+ear+'"/>';
  let head=kind==='bichon'?'<path d="M21 18q-3-13 10-12 9-9 16 0 14-3 13 10 13 6 4 18 5 13-10 15-7 12-17 3-15 7-19-8-12-4-5-17-6-9 8-9Z" fill="'+coat+'"/>':'<path d="M21 20q18-18 37 0 11 27-16 34-30-2-21-34Z" fill="'+coat+'"/>';
  const light=kind==='poodle'?'#f4e4c0':'#263c32';
  return `<svg viewBox="0 0 80 68" aria-hidden="true"><g stroke="#263c32" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round">${ears}${head}${kind==='corgi'?'<path d="m40 20-9 24 10 9 12-11Z" fill="#fff3d9" stroke="none"/>':''}<circle cx="30" cy="30" r="2" fill="${light}" stroke="none"/><circle cx="51" cy="30" r="2" fill="${light}" stroke="none"/><path d="m36 39 9 0-4 5Z" fill="${light}" stroke="none"/><path d="M41 44v4m-5-2q5 5 10 0" stroke="${light}" fill="none"/><path d="m26 55 28-1-11 10Z" fill="#cf5834"/></g></svg>`;
}

function scenery(){
  return `<defs><pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><path d="M0 0V9" stroke="#647a51" stroke-width="1" opacity=".19"/></pattern></defs>
  <path d="M36 158Q62 64 190 84T382 114Q489 51 590 138T665 332Q697 439 556 543T307 557Q203 605 126 497T60 337Q6 247 36 158Z" fill="#dce2c8" stroke="#a4b190" stroke-width="1.6" stroke-dasharray="5 7"/>
  <path d="M51 150Q146 72 238 152T387 182Q466 124 546 192L600 391 411 515 146 456 68 310Z" fill="url(#hatch)"/>
  <path d="M715 55q-76 47-49 142t-23 150q-48 51-10 111t-3 147h90Z" fill="#b9d0c5" opacity=".7"/>
  <path d="M688 73q-66 51-31 112t-15 127m13 191q16 49-4 83" stroke="#8eafa1" stroke-width="2" fill="none"/>
  <g class="doodle" opacity=".5" stroke-width="1.4"><path d="m40 495 8-14 9 14m-4-5 10-21 15 23M578 73l8-14 10 14M80 53l9-5m2 8 11-4M591 587l10-8m1 13 11-8"/></g>`;
}

const car=`<g class="doodle"><ellipse cx="0" cy="14" rx="31" ry="11" fill="#273e3022" stroke="none"/><path d="M-29-14q-4-9 9-11h36q13 1 14 12v26q-2 10-14 9h-32q-15 0-14-10Z" fill="#d9623b"/><path d="M-26-7h48v21h-48Z" fill="#efd39a"/><path d="m-16-7 6-13h14L17-7M-18 15v5m34-5v5"/><rect x="-30" y="-19" width="7" height="11" rx="2" fill="#263c32"/><rect x="-30" y="11" width="7" height="11" rx="2" fill="#263c32"/><rect x="22" y="-19" width="7" height="11" rx="2" fill="#263c32"/><rect x="22" y="11" width="7" height="11" rx="2" fill="#263c32"/><path d="m-16-4 7 0m2 0 7 0m2 0 7 0" stroke="#263c32"/><path d="M13-16h9m-1 31h6" stroke="#f9efce"/></g>`;
const gondola=`<g class="doodle"><path d="M0-29v11M-23-16h46v36h-46Z" fill="#e8b955"/><path d="M-18-11h12V5h-12ZM-1-11h12V5H-1Z" fill="#f8f5e7"/><path d="M-20 23h39"/></g>`;
const walker=`<g class="doodle"><circle cx="5" cy="-22" r="7" fill="#e9bc55"/><path d="M2-11 -8 5 1 14-7 31M2-11 11 4 22 11M-8 5-22 9M1 14 20 27" stroke="#263c32" stroke-width="5" fill="none"/><path d="m-2-9-8 13 11 8 8-12Z" fill="#cf5834"/></g>`;

