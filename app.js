'use strict';

const FILES = {
  players: 'players.csv', stats: 'stats.csv', teams: 'teams.csv', rules: 'tournaments_n_rules.csv',
  achievements: 'achievements.csv', hall: 'hall_of_fame.csv'
};
const STAT = {goals:'goals_on_date', assists:'assists_on_date', wins:'wins_on_date', draws:'draws_on_date', saves:'saves_on_date', foul:'foul_on_date'};
const COEFF = {goals:'goals_coefficient', assists:'assists_coefficient', wins:'wins_coefficient', draws:'draws_coefficient', saves:'saves_coefficient', foul:'foul_coefficient'};
const state = { data:{}, page:'home', tournament:null, season:null, section:'summary' };

const $ = s => document.querySelector(s);
const app = $('#app');

function parseCSV(text) {
  const rows=[]; let row=[], cell='', quoted=false;
  for(let i=0;i<text.length;i++) {
    const ch=text[i], next=text[i+1];
    if(ch==='"' && quoted && next==='"'){ cell+='"'; i++; }
    else if(ch==='"'){ quoted=!quoted; }
    else if(ch===',' && !quoted){ row.push(cell); cell=''; }
    else if((ch==='\n'||ch==='\r') && !quoted){
      if(ch==='\r'&&next==='\n') i++;
      row.push(cell); cell=''; if(row.some(v=>v!=='')) rows.push(row); row=[];
    } else cell+=ch;
  }
  if(cell.length||row.length){ row.push(cell); rows.push(row); }
  const headers=(rows.shift()||[]).map(x=>x.trim());
  return rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,(r[i]??'').trim()])));
}
async function loadCSV(path){ const r=await fetch(path,{cache:'no-store'}); if(!r.ok) throw new Error(`${path}: HTTP ${r.status}`); return parseCSV(await r.text()); }
const num=v=>Number(String(v??'').replace(',','.'))||0;
function textId(v){ return String(v??'').trim().replace(/\s+/g,' '); }
function idKey(v){ return textId(v).toLocaleLowerCase('ru-RU').replace(/ё/g,'е'); }
function date(v){ if(!v) return null; const d=new Date(v); return isNaN(d)?null:d; }
function fmtDate(v){ const d=v instanceof Date?v:date(v); return d?d.toLocaleDateString('ru-RU'):''; }
function escapeHTML(v){ return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function normalize(){
  for(const r of state.data.rules){ r.tournament_id=num(r.tournament_id); r.start=date(r.start); r.end=date(r.end); Object.values(COEFF).forEach(c=>r[c]=num(r[c])); }
  for(const key of ['stats','teams']) for(const r of state.data[key]) { if(r.tournament&&!r.tournament_id) r.tournament_id=r.tournament; r.tournament_id=num(r.tournament_id); r.date=date(r.date); r.team_number=num(r.team_number); Object.values(STAT).forEach(c=>r[c]=num(r[c])); }
  for(const r of state.data.achievements) r.achievement_id=num(r.achievement_id);
  for(const r of state.data.players) r.player_id=textId(r.player_id||r[Object.keys(r)[0]]);
  for(const r of state.data.hall){ r.achievement_id=num(r.achievement_id); r.player_id=textId(r.player_id); r.date=date(r.date); }
}
function table(rows, columns, options={}){
  if(!rows.length) return '<div class="card note">Данных пока нет.</div>';
  const cls=['table-wrap'];
  if(options.compact) cls.push('table-compact');
  if(options.className) cls.push(options.className);
  const attrs=options.id?` id="${escapeHTML(options.id)}"`:'';
  return `<div class="${cls.join(' ')}"${attrs}><table><thead><tr>${columns.map((c,i)=>`<th${options.sortable?` data-col="${i}" class="sortable"`:''}>${escapeHTML(c[1])}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${columns.map(c=>{const raw=typeof c[2]==='function'?c[2](r):r[c[0]]; return `<td>${c[3]==='html'?raw:escapeHTML(raw)}</td>`}).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function compareValues(a,b){
  if(a instanceof Date || b instanceof Date){
    const ta=a instanceof Date?a.getTime():new Date(a).getTime();
    const tb=b instanceof Date?b.getTime():new Date(b).getTime();
    if(Number.isFinite(ta)&&Number.isFinite(tb)) return ta-tb;
  }
  const sa=String(a??'').trim(), sb=String(b??'').trim();
  const na=Number(sa.replace(',','.')), nb=Number(sb.replace(',','.'));
  if(sa!==''&&sb!==''&&Number.isFinite(na)&&Number.isFinite(nb)) return na-nb;
  return sa.localeCompare(sb,'ru',{numeric:true,sensitivity:'base'});
}
function sortRows(rows,columns,sort){
  const col=columns.find(c=>c[0]===sort.key)||columns[0];
  const value=r=>typeof col[4]==='function'?col[4](r):(r[col[0]]);
  return rows.slice().sort((a,b)=>sort.dir*compareValues(value(a),value(b)));
}
function bindSortable(target,columns,sort,redraw){
  target.querySelectorAll('th.sortable').forEach((th,i)=>th.onclick=()=>{
    const key=columns[i][0];
    sort.dir=sort.key===key?-sort.dir:1; sort.key=key; redraw();
  });
}

function enableSorting(container, rows, columns, redraw){
  let sortIndex=0, direction=1;
  container.querySelectorAll('th.sortable').forEach(th=>th.onclick=()=>{
    const i=num(th.dataset.col); direction=sortIndex===i?-direction:1; sortIndex=i;
    const col=columns[i]; rows.sort((x,y)=>direction*compareValues(typeof col[2]==='function'?col[2](x):x[col[0]], typeof col[2]==='function'?col[2](y):y[col[0]]));
    redraw();
  });
}
function getRule(){ return state.data.rules.find(r=>r.tournament_name===state.tournament && String(r.season)===String(state.season)); }
function scope(rule){ const inside=r=>r.tournament_id===rule.tournament_id && r.date && r.date>=rule.start && r.date<=rule.end; return {stats:state.data.stats.filter(inside), teams:state.data.teams.filter(inside)}; }
function points(r,rule){ return Object.keys(STAT).reduce((s,k)=>s+num(r[STAT[k]])*num(rule[COEFF[k]]),0); }
function aggregate(stats,rule){ const map=new Map(); for(const r of stats){ const k=r.player_name||'Неизвестно'; if(!map.has(k)) map.set(k,{player_name:k,goals:0,assists:0,wins:0,draws:0,saves:0,foul:0,points:0}); const x=map.get(k); Object.keys(STAT).forEach(n=>x[n]+=num(r[STAT[n]])); x.points+=points(r,rule); } return [...map.values()].sort((a,b)=>b.points-a.points); }
function summary(stats,teams){ const wins=teams.reduce((s,r)=>s+num(r.wins_on_date),0); const draws=Math.floor(teams.reduce((s,r)=>s+num(r.draws_on_date),0)/2); return {games:wins+draws,draws,goals:stats.reduce((s,r)=>s+num(r.goals_on_date),0),assists:stats.reduce((s,r)=>s+num(r.assists_on_date),0),saves:stats.reduce((s,r)=>s+num(r.saves_on_date),0),fouls:stats.reduce((s,r)=>s+num(r.foul_on_date),0)}; }
function title(rule){ return `${escapeHTML(rule.season)} (${escapeHTML(String(rule.tournament_name).toUpperCase())})`; }

function setupMenu(){
  const pages=[['home','Главная'],['achievements','Достижения'],['analytics','Аналитика'],['tournaments','Турниры']];
  $('#main-menu').innerHTML=pages.map(([id,label])=>`<button data-page="${id}">${label}</button>`).join('');
  $('#main-menu').onclick=e=>{ const b=e.target.closest('button'); if(!b)return; state.page=b.dataset.page; render(); };
  $('#tournament-select').onchange=e=>{ state.tournament=e.target.value; fillSeasons(); render(); };
  $('#season-select').onchange=e=>{ state.season=e.target.value; render(); };
  $('#section-select').onchange=e=>{ state.section=e.target.value; render(); };
}
function fillFilters(){ const names=[...new Set(state.data.rules.map(r=>r.tournament_name))].sort(); if(!state.tournament) state.tournament=names[0]; $('#tournament-select').innerHTML=names.map(x=>`<option ${x===state.tournament?'selected':''}>${escapeHTML(x)}</option>`).join(''); fillSeasons(); $('#section-select').innerHTML=[['summary','Инфо.'],['top','Топ'],['games','Общая стат.'],['personal','Личная стат.']].map(([v,l])=>`<option value="${v}" ${v===state.section?'selected':''}>${l}</option>`).join(''); }
function fillSeasons(){ const seasons=state.data.rules.filter(r=>r.tournament_name===state.tournament).sort((a,b)=>b.start-a.start).map(r=>String(r.season)); if(!seasons.includes(String(state.season))) state.season=seasons[0]; $('#season-select').innerHTML=seasons.map(x=>`<option ${x===String(state.season)?'selected':''}>${escapeHTML(x)}</option>`).join(''); }

function renderHome(){
  const allRows=state.data.rules.slice().sort((a,b)=>b.start-a.start).map(rule=>{
    const scoped=scope(rule), s=summary(scoped.stats,scoped.teams);
    return {rule,place:rule.tournament_name,season:String(rule.season),start:rule.start,end:rule.end,games:s.games};
  });
  const filters={place:'',season:'',query:''};
  const sort={key:'start',dir:-1};
  const places=[...new Set(allRows.map(r=>r.place))].sort((a,b)=>a.localeCompare(b,'ru'));
  const seasons=[...new Set(allRows.map(r=>r.season))].sort((a,b)=>b.localeCompare(a,'ru',{numeric:true}));
  const columns=[
    ['place','Площадка'],['season','Сезон'],['start','Старт',r=>fmtDate(r.start),null,r=>r.start],
    ['end','Финиш',r=>fmtDate(r.end),null,r=>r.end],['games','Игр сыграно']
  ];
  app.innerHTML=`<h1>Футбол в МИТИНО</h1><h2>Сводная статистика по сезонам</h2>
    <div class="filter-panel home-filters">
      <label>Площадка<select id="home-place"><option value="">Все площадки</option>${places.map(x=>`<option>${escapeHTML(x)}</option>`).join('')}</select></label>
      <label>Сезон<select id="home-season"><option value="">Все сезоны</option>${seasons.map(x=>`<option>${escapeHTML(x)}</option>`).join('')}</select></label>
      <label>Поиск<input id="home-search" type="search" placeholder="Площадка или сезон..."></label>
      <button id="reset-home" class="secondary">Сбросить</button>
    </div><div id="home-count" class="table-meta"></div><div id="home-table"></div>
    <div class="note home-hint">Нажмите на строку, чтобы открыть общую статистику выбранного турнира.</div>
    <div class="footer">© MitinoSarayTeam</div>`;
  const draw=()=>{
    let rows=allRows.filter(r=>(!filters.place||r.place===filters.place)&&(!filters.season||r.season===filters.season)&&(!filters.query||`${r.place} ${r.season}`.toLowerCase().includes(filters.query.toLowerCase())));
    rows=sortRows(rows,columns,sort);
    $('#home-count').textContent=`Показано сезонов: ${rows.length}`;
    $('#home-table').innerHTML=table(rows,columns,{sortable:true,className:'clickable-table'});
    const target=$('#home-table'); bindSortable(target,columns,sort,draw);
    target.querySelectorAll('tbody tr').forEach((tr,i)=>{
      tr.tabIndex=0; tr.title='Открыть общую статистику';
      const open=()=>{const rule=rows[i].rule;state.tournament=rule.tournament_name;state.season=String(rule.season);state.section='games';state.page='tournaments';fillFilters();render();};
      tr.onclick=open; tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}};
    });
  };
  $('#home-place').onchange=e=>{filters.place=e.target.value;draw();};
  $('#home-season').onchange=e=>{filters.season=e.target.value;draw();};
  $('#home-search').oninput=e=>{filters.query=e.target.value.trim();draw();};
  $('#reset-home').onclick=()=>{filters.place='';filters.season='';filters.query='';$('#home-place').value='';$('#home-season').value='';$('#home-search').value='';draw();};
  draw();
}
function renderSummary(rule,stats,teams){
  const s=summary(stats,teams);
  const ruleNames={goals:'Гол',assists:'Пас',wins:'Победа',draws:'Ничья',saves:'На ноль',foul:'Фол'};
  const rulesText=Object.keys(STAT).map(k=>{ const value=num(rule[COEFF[k]]); const signed=value>0?`+${value}`:String(value); return `<li><span>${ruleNames[k]}</span><b>${signed}</b></li>`; }).join('');
  app.innerHTML=`<h1>${title(rule)}</h1><div class="summary-grid">${[['Игр сыграно',`${s.games} (ничьи: ${s.draws})`],['Голов забито',s.goals],['Пасов отдано',s.assists],['Shutout',s.saves],['Фолов',s.fouls]].map(x=>`<div class="metric"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join('')}<section class="metric rules-info"><div class="rules-info-title">Правила начисления очков</div><ul>${rulesText}</ul></section></div><div class="footer">© MitinoSarayTeam</div>`;
}
function renderTop(rule,stats){
  const a=aggregate(stats,rule);
  const sets=[['Общий рейтинг','points','Очки'],['Топ бомбардиров','goals','Голы'],['Топ раздающих','assists','Пасы'],['Топ голкиперов','saves','На ноль'],['Количество побед','wins','Побед'],['Количество ничьих','draws','Ничьих'],['Фолы','foul','Фолы']];
  app.innerHTML=`<h1>${title(rule)}</h1><div class="top-grid">`+sets.map(([h,k,l])=>`<section><h2>${h}</h2>${table(a.slice().sort((x,y)=>y[k]-x[k]),[['player_name','Игрок'],[k,l]],{compact:true})}</section>`).join('')+'</div>';
}
function renderGames(rule,stats){
  const dates=[...new Set(stats.filter(r=>r.date).map(r=>r.date.toISOString().slice(0,10)))].sort().reverse();
  const filters={date:dates[0]||'', player:'', team:'', query:''};
  let sort={key:'team_number',dir:1};
  const names=[...new Set(stats.map(r=>r.player_name).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'ru'));
  const teams=[...new Set(stats.map(r=>r.team_number))].sort((a,b)=>a-b);
  app.innerHTML=`<h1>${title(rule)}</h1><h2>Статистика игр по датам</h2>
    <div class="filter-panel">
      <label>Дата<select id="date-filter">${dates.map(d=>`<option value="${d}">${fmtDate(new Date(d+'T00:00:00'))}</option>`).join('')}</select></label>
      <label>Игрок<select id="player-filter"><option value="">Все игроки</option>${names.map(n=>`<option>${escapeHTML(n)}</option>`).join('')}</select></label>
      <label>Команда<select id="team-filter"><option value="">Все команды</option>${teams.map(n=>`<option value="${n}">${n}</option>`).join('')}</select></label>
      <label>Поиск<input id="games-search" type="search" placeholder="Имя игрока..."></label>
      <button id="reset-games" class="secondary">Сбросить</button>
    </div><div id="games-count" class="table-meta"></div><div id="games-table"></div>`;
  const columns=[['display_date','Число'],['team_number','№ команды'],['player_name','Игрок'],['goals_on_date','Голы'],['assists_on_date','Пасы'],['wins_on_date','Победы'],['draws_on_date','Ничьи'],['saves_on_date','На ноль'],['foul_on_date','Фолы'],['points','Очки']];
  const draw=()=>{
    let rows=stats.filter(r=>(!filters.date||r.date?.toISOString().slice(0,10)===filters.date)&&(!filters.player||r.player_name===filters.player)&&(!filters.team||String(r.team_number)===filters.team)&&(!filters.query||String(r.player_name).toLowerCase().includes(filters.query.toLowerCase())))
      .map(r=>({...r,display_date:fmtDate(r.date),points:points(r,rule)}));
    rows.sort((a,b)=>sort.dir*compareValues(a[sort.key],b[sort.key]));
    $('#games-count').textContent=`Показано строк: ${rows.length}`;
    $('#games-table').innerHTML=table(rows,columns,{sortable:true});
    $('#games-table').querySelectorAll('th.sortable').forEach((th,i)=>th.onclick=()=>{const key=columns[i][0]; sort={key,dir:sort.key===key?-sort.dir:1}; draw();});
  };
  $('#date-filter').onchange=e=>{filters.date=e.target.value;draw();};
  $('#player-filter').onchange=e=>{filters.player=e.target.value;draw();};
  $('#team-filter').onchange=e=>{filters.team=e.target.value;draw();};
  $('#games-search').oninput=e=>{filters.query=e.target.value.trim();draw();};
  $('#reset-games').onclick=()=>{filters.date=dates[0]||'';filters.player='';filters.team='';filters.query='';$('#date-filter').value=filters.date;$('#player-filter').value='';$('#team-filter').value='';$('#games-search').value='';draw();};
  draw();
}
function totals(rows){ const days=new Set(rows.map(r=>r.date?.toISOString().slice(0,10))).size||1; const x={days}; Object.keys(STAT).forEach(k=>x[k]=rows.reduce((s,r)=>s+num(r[STAT[k]]),0)); return x; }
function radarSVG(a,b,nameA,nameB){ const labels=['голы','пасы','победы','ничьи','на ноль','фолы']; const keys=['goals','assists','wins','draws','saves','foul']; const vals=[a,b].flatMap(x=>keys.map(k=>x[k]/x.days)); const max=Math.max(...vals,1); const cx=280,cy=245,R=180; const point=(i,v)=>{const ang=-Math.PI/2+i*Math.PI*2/6,r=R*v/max;return [cx+Math.cos(ang)*r,cy+Math.sin(ang)*r]}; const poly=x=>keys.map((k,i)=>point(i,x[k]/x.days).join(',')).join(' '); return `<svg viewBox="0 0 560 500" class="radar">${[.25,.5,.75,1].map(q=>`<polygon points="${keys.map((_,i)=>point(i,max*q).join(',')).join(' ')}" fill="none" stroke="#d8dee8"/>`).join('')}${keys.map((_,i)=>{const p=point(i,max); const lp=point(i,max*1.12); return `<line x1="${cx}" y1="${cy}" x2="${p[0]}" y2="${p[1]}" stroke="#d8dee8"/><text x="${lp[0]}" y="${lp[1]}" text-anchor="middle" font-size="14">${labels[i]}</text>`}).join('')}<polygon points="${poly(a)}" fill="rgba(220,38,38,.22)" stroke="#dc2626" stroke-width="3"/><polygon points="${poly(b)}" fill="rgba(234,179,8,.22)" stroke="#eab308" stroke-width="3"/><text x="20" y="28" fill="#dc2626">${escapeHTML(nameA)}</text><text x="20" y="50" fill="#b68a00">${escapeHTML(nameB)}</text></svg>`; }
function personalAchievements(playerName){
  const player=state.data.players.find(p=>idKey(p.player_name)===idKey(playerName));
  const playerId=player?textId(player.player_id||player[Object.keys(player)[0]]):'';
  const playerKey=idKey(playerId||playerName);
  const totalPlayers=new Set(state.data.players.map(p=>idKey(p.player_id||p[Object.keys(p)[0]])).filter(Boolean)).size;
  if(!playerKey) return '<div class="empty-achievements note">Не удалось сопоставить игрока с таблицей достижений.</div>';
  const records=state.data.hall.filter(h=>idKey(h.player_id)===playerKey).sort((a,b)=>(b.date||0)-(a.date||0)).slice(0,3);
  if(!records.length) return '<div class="empty-achievements note">У игрока пока нет достижений.</div>';
  return records.map(record=>{
    const achievement=state.data.achievements.find(a=>a.achievement_id===record.achievement_id)||{};
    const received=new Set(state.data.hall.filter(h=>h.achievement_id===record.achievement_id).map(h=>idKey(h.player_id)).filter(Boolean)).size;
    const image=achievement.image_path?`<img src="${escapeHTML(achievement.image_path)}" alt="${escapeHTML(achievement.achievement_name||'Достижение')}" onerror="this.outerHTML='<div class=&quot;mini-achievement-placeholder&quot;>🏆</div>'">`:'<div class="mini-achievement-placeholder">🏆</div>';
    const proof=record.proof_link?`<a class="proof-link" href="${escapeHTML(record.proof_link)}" target="_blank" rel="noopener noreferrer">ПРУФ</a>`:'<span class="proof-link disabled">ПРУФ отсутствует</span>';
    return `<article class="mini-achievement" data-achievement-id="${record.achievement_id}" tabindex="0" title="Открыть достижение">${image}<div class="mini-achievement-body"><h3>${escapeHTML(achievement.achievement_name||'Достижение')}</h3><div class="mini-achievement-date">Получено: ${fmtDate(record.date)}</div><div class="mini-achievement-count">Есть у ${received} из ${totalPlayers} игроков</div>${proof}</div></article>`;
  }).join('');
}
function renderPersonal(rule,stats){
  const names=[...new Set(stats.map(r=>r.player_name))].sort((a,b)=>a.localeCompare(b,'ru'));
  const sort={key:'display_date',dir:-1};
  const columns=[['display_date','Число',null,null,r=>r.date],['team_number','№ команды'],['goals_on_date','Голы'],['assists_on_date','Пасы'],['wins_on_date','Победы'],['draws_on_date','Ничьи'],['saves_on_date','На ноль'],['foul_on_date','Фолы'],['points','Очки']];
  app.innerHTML=`<h1>${title(rule)}</h1><div class="control-row"><label>Игрок<select id="player-a">${names.map(n=>`<option>${escapeHTML(n)}</option>`).join('')}</select></label><label>Сравнить с<select id="player-b">${names.map((n,i)=>`<option ${i===1?'selected':''}>${escapeHTML(n)}</option>`).join('')}</select></label></div><div id="personal"></div>`;
  const draw=()=>{
    const na=$('#player-a').value,nb=$('#player-b').value,ra=stats.filter(r=>r.player_name===na),rb=stats.filter(r=>r.player_name===nb),a=totals(ra),b=totals(rb);
    let rows=ra.map(r=>({...r,display_date:fmtDate(r.date),points:points(r,rule)})); rows=sortRows(rows,columns,sort);
    $('#personal').innerHTML=`<h2>Статистика по игроку: ${escapeHTML(na)}</h2><div class="card"><b>Побед:</b> ${a.wins} | <b>Ничьих:</b> ${a.draws} | <b>Голов:</b> ${a.goals} | <b>Пасов:</b> ${a.assists} | <b>На ноль:</b> ${a.saves} | <b>Фолов:</b> ${a.foul}</div><div id="personal-table">${table(rows,columns,{sortable:true})}</div><div class="personal-visual-grid"><section><h2>Пятиугольник силы</h2>${radarSVG(a,b,na,nb)}</section><aside class="recent-achievements"><h2>Последние достижения</h2><div id="recent-achievements-list">${personalAchievements(na)}</div></aside></div>`;
    bindSortable($('#personal-table'),columns,sort,draw);
    const list=$('#recent-achievements-list');
    if(list){
      list.onclick=e=>{if(e.target.closest('a'))return;const card=e.target.closest('[data-achievement-id]');if(card){state.page='achievements';renderAchievementDetail(num(card.dataset.achievementId));document.querySelectorAll('#main-menu button').forEach(b=>b.classList.toggle('active',b.dataset.page==='achievements'));}};
      list.onkeydown=e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('[data-achievement-id]')){e.preventDefault();state.page='achievements';renderAchievementDetail(num(e.target.dataset.achievementId));document.querySelectorAll('#main-menu button').forEach(b=>b.classList.toggle('active',b.dataset.page==='achievements'));}};
    }
  };
  $('#player-a').onchange=()=>{sort.key='display_date';sort.dir=-1;draw();}; $('#player-b').onchange=draw; draw();
}
function renderAchievements(){ const players=state.data.players, hall=state.data.hall, total=new Set(players.map(p=>p.player_id||p[Object.keys(p)[0]])).size; app.innerHTML=`<h1>Достижения</h1><p class="note">Зал славы участников и памятные футбольные достижения.</p><div id="ach-list">${state.data.achievements.sort((a,b)=>a.achievement_id-b.achievement_id).map(a=>{const got=new Set(hall.filter(h=>h.achievement_id===a.achievement_id).map(h=>h.player_id)).size,pct=total?got/total*100:0,img=a.image_path?`<img src="${escapeHTML(a.image_path)}" onerror="this.outerHTML='<div class=&quot;achievement-placeholder&quot;>🏆</div>'">`:'<div class="achievement-placeholder">🏆</div>'; return `<div class="achievement-card" data-id="${a.achievement_id}">${img}<div><h3>${escapeHTML(a.achievement_name)}</h3><div>${escapeHTML(a.description)}</div><div class="progress">Получили: ${got} из ${total} игроков — ${pct.toFixed(1)}%</div></div></div>`}).join('')}</div>`; $('#ach-list').onclick=e=>{const c=e.target.closest('[data-id]'); if(c) renderAchievementDetail(num(c.dataset.id));}; }
function renderAchievementDetail(id){
  const a=state.data.achievements.find(x=>x.achievement_id===id);
  const names=new Map(state.data.players.map(p=>[idKey(p.player_id||p[Object.keys(p)[0]]),p.player_name]));
  const rows=state.data.hall.filter(h=>h.achievement_id===id).sort((x,y)=>(y.date||0)-(x.date||0)).map(h=>({
    name:names.get(idKey(h.player_id))||h.player_id,
    date:fmtDate(h.date),
    url:String(h.proof_link||'').trim()
  }));
  const proofColumn=['proof','Видео',r=>r.url?`<a class="table-proof-link" href="${escapeHTML(r.url)}" target="_blank" rel="noopener noreferrer">ПРУФ ↗</a>`:'—','html'];
  app.innerHTML=`<button id="back-ach" class="back-link" type="button"><span aria-hidden="true">←</span><span>К списку достижений</span></button><h1>${escapeHTML(a?.achievement_name||'Достижение')}</h1><p>${escapeHTML(a?.description||'')}</p>${a?.image_path?`<img src="${escapeHTML(a.image_path)}" class="achievement-detail-image" alt="${escapeHTML(a?.achievement_name||'Достижение')}">`:''}<h2>Обладатели достижения</h2>${table(rows,[['name','Игрок'],['date','Дата'],proofColumn])}`;
  $('#back-ach').onclick=renderAchievements;
}
function estimatedGames(statsRow, teamRows){
  const same=teamRows.filter(t=>t.tournament_id===statsRow.tournament_id && t.date?.toISOString().slice(0,10)===statsRow.date?.toISOString().slice(0,10));
  if(!same.length) return 1;
  const wins=same.reduce((s,r)=>s+num(r.wins_on_date),0), draws=same.reduce((s,r)=>s+num(r.draws_on_date),0)/2;
  const totalGames=wins+draws, marks=same.reduce((s,r)=>s+num(r.wins_on_date)+num(r.draws_on_date),0);
  const losses=Math.max(totalGames*2-marks,0);
  const maxStrength=Math.max(...same.map(r=>num(r.wins_on_date)+num(r.draws_on_date)),0);
  const weights=same.map(r=>maxStrength-(num(r.wins_on_date)+num(r.draws_on_date))+1), weightSum=weights.reduce((a,b)=>a+b,0)||1;
  const idx=same.findIndex(r=>r.team_number===statsRow.team_number);
  if(idx<0) return 1;
  return num(same[idx].wins_on_date)+num(same[idx].draws_on_date)+losses*weights[idx]/weightSum;
}
function bayes(value,games,avg,k=10){return games/(games+k)*value+k/(games+k)*avg;}
function reliability(g){return g>=30?'высокая':g>=10?'средняя':'низкая';}
function archetype(r){if(r.goals>=r.assists*1.5&&r.goals>=5)return'Снайпер';if(r.assists>=r.goals*1.4&&r.assists>=5)return'Плеймейкер';if(r.saves>=Math.max(r.goals,r.assists)&&r.saves>=3)return'Голкипер';if(r.teamImpact>=.75&&r.attackSkill<.65)return'Командный';if(r.attackSkill>=.65&&r.teamImpact>=.70)return'Универсал';if(r.discipline>=.95&&r.teamImpact>=.65)return'Надежный';return'Сбалансированный';}
function bayesianOverall(stats,teams){
  const map=new Map();
  for(const r of stats){const n=r.player_name||'Неизвестно';if(!map.has(n))map.set(n,{player_name:n,games:0,goals:0,assists:0,saves:0,foul:0,wins:0,draws:0});const x=map.get(n);x.games+=estimatedGames(r,teams);x.goals+=num(r.goals_on_date);x.assists+=num(r.assists_on_date);x.saves+=num(r.saves_on_date);x.foul+=num(r.foul_on_date);x.wins+=num(r.wins_on_date);x.draws+=num(r.draws_on_date);}
  const rows=[...map.values()].filter(x=>x.games>0); const tg=rows.reduce((s,x)=>s+x.games,0)||1;
  const attackAvg=rows.reduce((s,x)=>s+x.goals*3+x.assists*4+x.saves*3-x.foul,0)/tg, teamAvg=rows.reduce((s,x)=>s+x.wins+.5*x.draws,0)/tg, foulAvg=rows.reduce((s,x)=>s+x.foul,0)/tg;
  rows.forEach(x=>{x.attackPerGame=(x.goals*3+x.assists*4+x.saves*3-x.foul)/x.games;x.teamPerGame=(x.wins+.5*x.draws)/x.games;x.foulPerGame=x.foul/x.games;x.attackBayes=bayes(x.attackPerGame,x.games,attackAvg);x.teamBayes=bayes(x.teamPerGame,x.games,teamAvg);x.foulBayes=bayes(x.foulPerGame,x.games,foulAvg);});
  const maxAttack=Math.max(...rows.map(x=>x.attackBayes),1), maxFoul=Math.max(...rows.map(x=>x.foulBayes),0);
  rows.forEach(x=>{x.attackSkill=Math.max(0,Math.min(1,x.attackBayes/maxAttack));x.teamImpact=Math.max(0,Math.min(1,x.teamBayes));x.discipline=maxFoul<=0?1:Math.max(0,Math.min(1,1-x.foulBayes/maxFoul));x.overall=.55*x.attackSkill+.35*x.teamImpact+.10*x.discipline;x.reliability=reliability(x.games);x.type=archetype(x);});
  return rows.sort((a,b)=>b.overall-a.overall||b.attackSkill-a.attackSkill);
}
function partnersFor(stats,teams,player,rules,rule){
  const enriched=stats.map(r=>({...r,points:rule?points(r,rule):points(r,rules.find(x=>x.tournament_id===r.tournament_id)||{}),games:estimatedGames(r,teams)}));
  const selected=enriched.filter(r=>r.player_name===player), result=new Map();
  for(const me of selected){for(const p of enriched){if(p.player_name===player||p.tournament_id!==me.tournament_id||p.team_number!==me.team_number||p.date?.toISOString().slice(0,10)!==me.date?.toISOString().slice(0,10))continue;const n=p.player_name;if(!result.has(n))result.set(n,{partner:n,games:0,wins:0,draws:0,ga:0,points:0});const x=result.get(n);x.games+=me.games;x.wins+=num(me.wins_on_date);x.draws+=num(me.draws_on_date);x.ga+=num(me.goals_on_date)+num(me.assists_on_date)+num(p.goals_on_date)+num(p.assists_on_date);x.points+=me.points+p.points;}}
  const rows=[...result.values()];rows.forEach(x=>x.ppg=x.points/Math.max(x.games,1));const mg=Math.max(...rows.map(x=>x.games),1),mp=Math.max(...rows.map(x=>x.ppg),1);rows.forEach(x=>x.index=.5*Math.min(1,x.games/mg)+.5*Math.max(0,Math.min(1,x.ppg/mp)));return rows.sort((a,b)=>b.index-a.index||b.games-a.games);
}
function analyticsPeriods(){const list=[{label:'За все время',id:null}];state.data.rules.slice().sort((a,b)=>b.start-a.start).forEach(r=>list.push({label:`${r.season} — ${r.tournament_name}`,id:r.tournament_id}));return list;}
function renderAnalytics(){
  const periods=analyticsPeriods();
  const ratingSort={key:'overall',dir:-1}, partnerSort={key:'index',dir:-1};
  app.innerHTML=`<h1>Аналитика</h1><div class="control-row"><label>Выберите сезон<select id="analytics-period">${periods.map(p=>`<option value="${p.id??''}">${escapeHTML(p.label)}</option>`).join('')}</select></label></div><div id="analytics-body"></div>`;
  const draw=()=>{
    const id=num($('#analytics-period').value),rule=id?state.data.rules.find(r=>r.tournament_id===id):null,scoped=rule?scope(rule):{stats:state.data.stats,teams:state.data.teams};
    const baseRows=bayesianOverall(scoped.stats,scoped.teams);
    const columns=[['player_name','Игрок'],['overall','Overall',r=>r.overall.toFixed(3)],['attackSkill','Attack Skill',r=>r.attackSkill.toFixed(3)],['teamImpact','Team Impact',r=>r.teamImpact.toFixed(3)],['discipline','Discipline',r=>r.discipline.toFixed(3)],['games','Игры',r=>Math.ceil(r.games)],['reliability','Надежность'],['type','Тип'],['goals','Голы'],['assists','Пасы'],['saves','На ноль'],['foul','Фолы'],['wins','Победы'],['draws','Ничьи']];
    const drawRating=()=>{
      const rows=sortRows(baseRows,columns,ratingSort);
      $('#rating-table').innerHTML=table(rows,columns,{sortable:true,className:'analytics-table'});
      bindSortable($('#rating-table'),columns,ratingSort,drawRating);
    };
    $('#analytics-body').innerHTML=`<div class="formula-card"><h2>Overall Skill Index</h2><div class="formula-main">Overall = 0.55 × Attack Skill + 0.35 × Team Impact + 0.10 × Discipline</div><div class="formula-grid"><div><b>Attack Skill</b><span>Голы, передачи, игры на ноль и фолы в расчёте на игру с Bayesian correction.</span></div><div><b>Team Impact</b><span>Победы и половина ничьих в расчёте на игру.</span></div><div><b>Discipline</b><span>Чем меньше фолов за игру, тем выше показатель.</span></div></div></div><h2>Рейтинг игроков</h2><div id="rating-table"></div><h2>Предпочтительные партнеры</h2><div class="control-row"><label>Игрок<select id="partner-player">${baseRows.map(r=>`<option>${escapeHTML(r.player_name)}</option>`).join('')}</select></label></div><div id="partners-table"></div>`;
    drawRating();
    const partnerColumns=[['partner','Партнер'],['index','Индекс связки',r=>r.index.toFixed(3)],['games','Игр вместе',r=>Math.ceil(r.games)],['wins','Побед вместе'],['draws','Ничьих вместе'],['ga','Голы+пасы пары'],['points','Очки пары',r=>r.points.toFixed(2)],['ppg','Очки пары/игру',r=>r.ppg.toFixed(3)]];
    const drawPartners=()=>{
      const player=$('#partner-player').value,basePartners=partnersFor(scoped.stats,scoped.teams,player,state.data.rules,rule),p=sortRows(basePartners,partnerColumns,partnerSort);
      $('#partners-table').innerHTML=table(p,partnerColumns,{compact:true,sortable:true}); bindSortable($('#partners-table'),partnerColumns,partnerSort,drawPartners);

    };
    $('#partner-player').onchange=()=>{partnerSort.key='index';partnerSort.dir=-1;drawPartners();}; drawPartners();
  };
  $('#analytics-period').onchange=()=>{ratingSort.key='overall';ratingSort.dir=-1;partnerSort.key='index';partnerSort.dir=-1;draw();}; draw();
}
function renderTournament(){ const rule=getRule(); if(!rule){app.innerHTML='<div class="card">Турнир не выбран.</div>';return;} const {stats,teams}=scope(rule); if(state.section==='summary')renderSummary(rule,stats,teams); else if(state.section==='top')renderTop(rule,stats); else if(state.section==='games')renderGames(rule,stats); else renderPersonal(rule,stats); }
function render(){ document.querySelectorAll('#main-menu button').forEach(b=>b.classList.toggle('active',b.dataset.page===state.page)); $('#tournament-filters').classList.toggle('hidden',state.page!=='tournaments'); if(state.page==='home')renderHome(); else if(state.page==='achievements')renderAchievements(); else if(state.page==='analytics')renderAnalytics(); else renderTournament(); }
async function init(){ try { setupMenu(); const entries=await Promise.all(Object.entries(FILES).map(async([k,p])=>[k,await loadCSV(p)])); state.data=Object.fromEntries(entries); normalize(); fillFilters(); $('#status').classList.add('hidden'); render(); } catch(e){ $('#status').className='status error'; $('#status').innerHTML=`Не удалось загрузить CSV: <b>${escapeHTML(e.message)}</b><br>Откройте сайт через локальный сервер, а не двойным кликом по index.html.`; console.error(e); } }
init();
