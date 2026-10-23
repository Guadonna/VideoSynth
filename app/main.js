import {OSC_NAMES,SOURCES,MODES,initialState,countRoutes,toggleRoute,moveCursor,slotButton,toggleOsc,toggleScreen,validateState,preset,cvModel} from './model.js';
import {VIDEO,raster,codeVoltage} from './video.js';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
let state=preset('weave'),running=true,ready=false,field='both',currentTab='instrument',lastLuma=null,lastRgba=null,frames=0,firstFrame=0,lastFrame=0;
const output=$('#output').getContext('2d',{alpha:false}),preview=$('#preview').getContext('2d',{alpha:false});
const frameCanvas=document.createElement('canvas');frameCanvas.width=720;frameCanvas.height=480;const frameContext=frameCanvas.getContext('2d',{alpha:false});
let toastTimer;
function toast(message){$('#toast').textContent=message;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),2800);}
function send(){if(ready)worker.postMessage({type:'state',state});}
const workerURL=globalThis.EMBEDDED_WORKER?URL.createObjectURL(new Blob([globalThis.EMBEDDED_WORKER],{type:'text/javascript'})):new URL('./render-worker.js',import.meta.url);
const worker=new Worker(workerURL,{type:'module'});
worker.onerror=e=>{$('#loading').textContent='Ошибка DSP: '+e.message;toast('Не удалось запустить DSP. Откройте приложение через npm start или standalone HTML.');};
worker.onmessage=({data})=>{
 if(data.type==='ready'){ready=true;send();return;}
 if(data.type==='error'){$('#loading').textContent=data.message;return;}
 if(data.type!=='frame')return;
 lastLuma=data.luma;lastRgba=data.rgba;frames++;lastFrame=data.frame;
 if(!firstFrame)firstFrame=performance.now();
 frameContext.putImageData(new ImageData(data.rgba,720,480),0,0);drawOutput();
 if(state.screen==='preview')preview.drawImage(frameCanvas,0,0,320,240);
 $('#loading').hidden=true;
 if(frames%5===0){const fps=frames/((performance.now()-firstFrame)/1000);$('#engine-metrics').textContent=`PC: ${data.renderMs.toFixed(1)} мс / ${Math.min(fps,100).toFixed(1)} кадр/с`;}
 if(currentTab==='checks'&&frames%5===0)drawScope();
};
function drawOutput(){
 if(!lastRgba)return;
 if(field==='both')output.drawImage(frameCanvas,0,0);
 else{
  output.fillStyle='#0a1012';output.fillRect(0,0,720,480);
  for(let y=Number(field);y<480;y+=2)output.drawImage(frameCanvas,0,y,720,1,0,y,720,1);
 }
}
const params=[{key:'frequency',label:'FREQ',min:.25,max:64,step:.05,format:v=>v.toFixed(2)}, {key:'fine',label:'FINE',min:-1,max:1,step:.01,format:v=>(v>=0?'+':'')+v.toFixed(2)}, {key:'phase',label:'PHASE',min:0,max:1,step:1/360,format:v=>Math.round(v*360)+'°'}, {key:'morph',label:'MORPH',min:0,max:3,step:.01,format:v=>['SIN','TRI','SAW','SQR'][Math.min(3,Math.floor(v))]+(v%1>.01?' ↔':'')}];
$('#osc-bank').innerHTML=OSC_NAMES.map((name,i)=>`<section class="oscillator ${i>2?'vertical':''}" aria-label="Осциллятор ${name}"><div class="osc-title">${name}<small>${i<3?'AXIS X':'AXIS Y'}</small></div><div class="knob-grid">${params.map(p=>`<label class="knob-control"><span class="knob-label">${p.label}</span><span class="knob-shell"><span class="knob-dial" id="dial-${i}-${p.key}"></span><input type="range" id="osc-${i}-${p.key}" data-osc="${i}" data-param="${p.key}" aria-label="${name} ${p.label}" min="${p.min}" max="${p.max}" step="${p.step}"></span><output id="value-${i}-${p.key}"></output></label>`).join('')}</div><button class="osc-toggle" data-toggle="${i}" aria-label="${name}: участие в миксе" aria-pressed="false"><i></i><span>В МИКС</span></button></section>`).join('');
for(const input of $$('[data-param]')){
 input.addEventListener('input',()=>{state.osc[+input.dataset.osc][input.dataset.param]=+input.value;updateKnobs();send();});
 input.addEventListener('wheel',e=>{e.preventDefault();input.value=String(Math.min(+input.max,Math.max(+input.min,+input.value+(e.deltaY<0?1:-1)*+input.step)));input.dispatchEvent(new Event('input'));},{passive:false});
 let drag=null;
 input.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();input.focus();drag={x:e.clientX,y:e.clientY,value:+input.value};input.setPointerCapture(e.pointerId);});
 input.addEventListener('pointermove',e=>{if(!drag)return;const unit=(+input.max-input.min)/180;const value=drag.value+(drag.y-e.clientY+(e.clientX-drag.x)*.3)*unit;input.value=String(Math.min(+input.max,Math.max(+input.min,value)));input.dispatchEvent(new Event('input'));});
 input.addEventListener('pointerup',()=>drag=null);input.addEventListener('pointercancel',()=>drag=null);
 input.addEventListener('dblclick',()=>{input.value=initialState().osc[+input.dataset.osc][input.dataset.param];input.dispatchEvent(new Event('input'));});
}
function updateKnobs(){
 for(let i=0;i<6;i++)for(const p of params){const v=state.osc[i][p.key];$(`#osc-${i}-${p.key}`).value=v;$(`#value-${i}-${p.key}`).textContent=p.format(v);$(`#dial-${i}-${p.key}`).style.setProperty('--angle',(-135+270*(v-p.min)/(p.max-p.min))+'deg');}
 for(const b of $$('[data-toggle]')){const on=state.osc[+b.dataset.toggle].mixed;b.setAttribute('aria-pressed',String(on));b.querySelector('span').textContent=on?'В МИКСЕ':'В МИКС';}
}
for(const b of $$('[data-toggle]'))b.onclick=()=>{toggleOsc(state,+b.dataset.toggle);updateKnobs();send();};
$('#matrix').className='matrix-grid';
$('#matrix').innerHTML='<span></span>'+OSC_NAMES.map((n,i)=>`<div class="matrix-group ${i>2?'vertical':''}">${n}</div>`).join('')+'<span></span>'+Array.from({length:18},(_,i)=>`<span class="matrix-type">${MODES[i%3]}</span>`).join('')+SOURCES.map((s,y)=>`<span class="matrix-row-label">${s}</span>`+Array.from({length:18},(_,x)=>`<button class="matrix-cell ${x>=9?'vertical':''}" role="gridcell" tabindex="-1" data-x="${x}" data-y="${y}" aria-label="${s} → ${OSC_NAMES[Math.floor(x/3)]} ${MODES[x%3]}" aria-pressed="false"></button>`).join('')).join('');
for(const cell of $$('.matrix-cell'))cell.onclick=()=>{
 state.cursor={x:+cell.dataset.x,y:+cell.dataset.y};const r=toggleRoute(state);if(!r.ok)toast(r.message);updateMatrix();send();
};
function updateMatrix(){
 const n=countRoutes(state);$('#route-count').textContent=`${n} / 36`;
 for(const cell of $$('.matrix-cell')){const {x,y}=cell.dataset,on=state.matrix[y][x],selected=+x===state.cursor.x&&+y===state.cursor.y;cell.classList.toggle('on',on);cell.classList.toggle('selected',selected);cell.setAttribute('aria-pressed',String(on));cell.tabIndex=selected?0:-1;}
 const {x,y}=state.cursor;$('#selection').textContent=`${SOURCES[y]} → ${OSC_NAMES[Math.floor(x/3)]} · ${MODES[x%3]}`;$('#slot-state').textContent=state.matrix[y][x]?'ВКЛ':'ВЫКЛ';$('#slot-state').style.color=state.matrix[y][x]?'#e7b46c':'';$('#x-value').textContent=String(x+1).padStart(2,'0');$('#y-value').textContent=String(y+1).padStart(2,'0');
 $('#matrix-screen').hidden=state.screen!=='matrix';$('#preview-screen').hidden=state.screen!=='preview';$('#screen-title').textContent=state.screen==='matrix'?'MODULATION MATRIX':'OUTPUT PREVIEW';$('#slot').disabled=state.screen!=='matrix';
 if(state.screen==='preview'&&lastRgba)preview.drawImage(frameCanvas,0,0,320,240);
}
function cursor(dx,dy){if(state.screen!=='matrix')return;moveCursor(state,dx,dy);updateMatrix();}
for(const [id,dx,dy] of [['x-minus',-1,0],['x-plus',1,0],['y-minus',0,-1],['y-plus',0,1]])$('#'+id).onclick=()=>cursor(dx,dy);
$('#enc-x').onclick=()=>cursor(1,0);$('#enc-y').onclick=()=>cursor(0,1);
for(const [id,axis] of [['enc-x','x'],['enc-y','y']])$('#'+id).addEventListener('wheel',e=>{e.preventDefault();cursor(axis==='x'?(e.deltaY<0?1:-1):0,axis==='y'?(e.deltaY<0?1:-1):0);},{passive:false});
$('#mode').onclick=()=>{toggleScreen(state);updateMatrix();};
$('#slot').onclick=()=>{const r=slotButton(state);if(!r.ok)toast(r.message);updateMatrix();send();};
window.addEventListener('keydown',e=>{
 if($('#help-dialog').open||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)||currentTab!=='instrument')return;
 if(e.key.toLowerCase()==='m'){e.preventDefault();$('#mode').click();}
 else if(/^[1-6]$/.test(e.key)){e.preventDefault();$(`[data-toggle="${+e.key-1}"]`).click();}
 else if(state.screen==='matrix'){
  const map={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
  if(map[e.key]){e.preventDefault();cursor(...map[e.key]);if(e.target.matches('.matrix-cell'))$('.matrix-cell.selected').focus();}
  else if(e.code==='Space'&&!e.target.matches('button:not(.matrix-cell)')){e.preventDefault();$('#slot').click();}
 }
});
$('#cv-controls').innerHTML=[0,1].map(i=>`<div class="cv-control"><h3>CV${i+1}</h3><div class="cv-head"><select data-cv="${i}" data-cv-param="mode" aria-label="CV${i+1} источник"><option value="0">Постоянное напряжение</option><option value="1">Синусоидальный LFO</option></select><span class="eyebrow">−10…+10 V</span></div><label>Смещение<input type="range" min="-15" max="15" step=".1" data-cv="${i}" data-cv-param="volts" aria-label="CV${i+1} напряжение"><output id="cv-${i}-volts"></output></label><label>Частота LFO<input type="range" min="0" max="100" step=".1" data-cv="${i}" data-cv-param="frequency" aria-label="CV${i+1} частота"><output id="cv-${i}-frequency"></output></label><span></span><label>Амплитуда LFO<input type="range" min="0" max="10" step=".1" data-cv="${i}" data-cv-param="amplitude" aria-label="CV${i+1} амплитуда"><output id="cv-${i}-amplitude"></output></label></div>`).join('');
for(const c of $$('[data-cv]'))c.addEventListener(c.tagName==='SELECT'?'change':'input',()=>{state.cv[+c.dataset.cv][c.dataset.cvParam]=+c.value;updateCV();send();});
function updateCV(){
 for(const c of $$('[data-cv]')){const v=state.cv[+c.dataset.cv][c.dataset.cvParam];c.value=v;if(c.tagName!=='SELECT'){const unit=c.dataset.cvParam==='frequency'?'Гц':'В';$(`#cv-${c.dataset.cv}-${c.dataset.cvParam}`).textContent=v.toFixed(1)+' '+unit;c.disabled=c.dataset.cvParam!=='volts'&&state.cv[+c.dataset.cv].mode===0;}}
 $('#cv-readout').replaceChildren(...state.cv.map((c,i)=>{const m=cvModel(c.volts),el=document.createElement('dl');el.innerHTML=`<dt>CV${i+1} DC</dt><dd>${c.volts.toFixed(1)} В</dd><dt>На входе АЦП</dt><dd>${m.voltage.toFixed(3)} В / ${m.code}</dd><dt>Диапазон</dt><dd class="${m.overload?'amber':''}">${m.overload?'Перегрузка · испытать':'Рабочий ±10 В'}</dd>`;return el;}));
}
function refresh(){updateKnobs();updateMatrix();updateCV();send();}
$('#preset').onchange=()=>{state=preset($('#preset').value);worker.postMessage({type:'resetTime'});refresh();toast('Сцена загружена');};
$('#pause').onclick=()=>{running=!running;worker.postMessage({type:'running',running});$('#pause').textContent=running?'Пауза':'Продолжить';$('#on-air').textContent=running?'● LIVE':'Ⅱ HOLD';if(running){frames=0;firstFrame=0;}};
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1500);}
$('#save').onclick=()=>download(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),'VideoSynth-preset.json');
$('#load').onclick=()=>$('#file').click();
$('#file').onchange=async()=>{const file=$('#file').files[0];if(!file)return;try{if(file.size>65536)throw Error('Файл больше 64 КБ');const next=validateState(JSON.parse(await file.text()));state=next;refresh();toast('Пресет открыт');}catch(e){toast('Пресет отклонён: '+e.message);}$('#file').value='';};
$('#png').onclick=()=>{if(!lastRgba){toast('Дождитесь первого кадра');return;}frameCanvas.toBlob(blob=>download(blob,`VideoSynth-${lastFrame}.png`));};
$('#raw').onclick=()=>{if(!lastLuma)return;download(new Blob([raster(lastLuma)],{type:'application/octet-stream'}),'VideoSynth-525-27MSPS-u8.bin');toast('900 900 отсчётов: полный кадр 525 строк');};
for(const b of $$('[data-field]'))b.onclick=()=>{field=b.dataset.field;for(const q of $$('[data-field]'))q.classList.toggle('active',q===b);drawOutput();};
for(const t of $$('.tab'))t.onclick=()=>{currentTab=t.dataset.tab;for(const q of $$('.tab'))q.classList.toggle('active',q===t);for(const section of $$('.tab-content'))section.hidden=section.id!==currentTab;if(currentTab==='checks')drawScope();};
$('#help').onclick=()=>$('#help-dialog').showModal();$('#close-help').onclick=()=>$('#help-dialog').close();$('#help-dialog').onclick=e=>{if(e.target===$('#help-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}};
const blocks={
 power:['Питание Eurorack','+12 В → предохранитель 750 мА → SS34 → TPS54302 → 5 В. Отрицательная шина не используется. Питание модуля подаётся на POE_PWR1, выводы 4/3. На модуле обязательно удалить FET2: иначе USB сможет питать устройство.','Проверить: запуск, ток, пульсации, нагрев, переполюсовку и отсутствие обратного питания.'],
 mcu:['ESP32-P4 на модуле Olimex','DevKit Rev.D1: два ядра, 32 МБ PSRAM, внешняя Flash. GPIO9…16 → видеоданные; GPIO17 → внешний 27-МГц clock. SPI обслуживает MCP3204 и дисплей; I²C — два MCP23017 на панели.','Проверить: фактическую ревизию чипа, PARLIO/DMA и 36 связей при одновременной работе UI. Код эмулятора не является готовой прошивкой платы.'],
 dac:['ЦАП AD9708','8-битный параллельный ЦАП. Rset = 1,91 кОм, нагрузка 49,9 Ом. Коды: синхронизация 0, чёрный 73, белый 255. Данные должны выдаваться на противоположном фронте относительно захвата ЦАП.','Проверить осциллографом setup/hold, джиттер и порядок битов. Хост-модель кодирует растр, но не моделирует электрический PARLIO.'],
 video:['Композитный выход','THS7314: усиление ×2, ФНЧ 8,5 МГц, последовательные 75 Ом и внешняя нагрузка 75 Ом. Один RCA подключается коротким коаксиалом. Нет цветового burst.','Расчётный размах ≈1 В на нагрузке, смещение синхровершины ≈143 мВ из-за буфера. Приёмник восстанавливает уровень. Фильтрация и реальная полоса требуют испытаний.']
};
function showBlock(key){const [title,text,note]=blocks[key];$('#block-details').innerHTML=`<h3>${title}</h3><p>${text}</p><p class="muted">${note}</p>`;}
for(const b of $$('[data-block]'))b.onclick=()=>showBlock(b.dataset.block);showBlock('power');
function drawScope(){
 if(!lastLuma)return;
 const r=raster(lastLuma),ctx=$('#scope').getContext('2d'),W=800,H=280,left=48,top=22,w=730,h=210;
 ctx.fillStyle='#121b20';ctx.fillRect(0,0,W,H);ctx.font='10px monospace';ctx.lineWidth=1;
 for(let i=0;i<=4;i++){const y=top+h-i*h/4;ctx.strokeStyle='#2b3c42';ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(left+w,y);ctx.stroke();ctx.fillStyle='#82979d';ctx.fillText((i*.25).toFixed(2),8,y+4);}
 for(let i=0;i<=6;i++){const x=left+i*w/6;ctx.strokeStyle='#223239';ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+h);ctx.stroke();ctx.fillStyle='#82979d';ctx.fillText((i*10.5926).toFixed(1),x-9,253);}
 ctx.strokeStyle='#e7b46c';ctx.lineWidth=1.3;ctx.beginPath();const base=22*1716;
 for(let i=0;i<1716;i++){const x=left+i*w/1716,y=top+h-codeVoltage(r[base+i])*h;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();ctx.fillStyle='#d9c29e';ctx.fillText('В',12,15);ctx.fillText('мкс',755,269);
}
async function selfTest(){
 $('#self-test').disabled=true;$('#test-results').textContent='Расчёт…';const results=[];
 const test=(name,fn)=>{try{if(!fn())throw Error('assertion');results.push([name,true]);}catch{results.push([name,false]);}};
 try{
  const bytes=globalThis.WASM_BASE64?Uint8Array.from(atob(globalThis.WASM_BASE64),c=>c.charCodeAt(0)):await (await fetch('./assets/engine.wasm')).arrayBuffer();
  const api=(await WebAssembly.instantiate(bytes,{})).instance.exports;api.reset_state();
  test('37-я связь отклоняется',()=>{for(let i=0;i<36;i++)if(api.set_route(Math.floor(i/18),i%18,1))return false;return api.route_count()===36&&api.set_route(2,0,1)===-2;});
  test('36 связей: полный кадр 720×480',()=>api.render_frame(0)===345600);
  api.reset_state();for(let i=0;i<6;i++)api.set_osc(i,8,0,0,0,0);
  test('Пустой микс даёт чёрное изображение',()=>{api.render_frame(0);return new Uint8Array(api.memory.buffer,api.luma_ptr(),345600).every(x=>x===0);});
  test('Чёрный кадр сохраняет синхронизацию',()=>{const r=raster(new Uint8Array(345600));return r.length===900900&&r[22*1716]===0&&r[22*1716+244]===73;});
  test('SLOT не изменяет матрицу в preview',()=>{const s=initialState();s.screen='preview';slotButton(s);return countRoutes(s)===0;});
  test('OSC-кнопка не удаляет связи',()=>{const s=initialState();s.matrix[0][3]=true;toggleOsc(s,0);return !s.osc[0].mixed&&s.matrix[0][3];});
  test('Два поля по 262,5 строки',()=>VIDEO.fieldSamples===1716*262.5&&VIDEO.frameSamples===2*VIDEO.fieldSamples);
 }catch(e){results.push(['Загрузка DSP: '+e.message,false]);}
 $('#test-results').replaceChildren(...results.map(([name,ok])=>{const div=document.createElement('div');div.className='test-row';const text=document.createElement('span');text.textContent=name;const badge=document.createElement('span');badge.className=ok?'pass':'fail';badge.textContent=ok?'✓ PASS':'✕ FAIL';div.append(text,badge);return div;}));$('#self-test').disabled=false;
}
$('#self-test').onclick=selfTest;
async function loadVerification(){try{const v=globalThis.VERIFICATION||await (await fetch('./assets/verification.json')).json();$('#verification').replaceChildren(...v.checks.map(c=>{const div=document.createElement('div');div.className='verification-line';const label=document.createElement('span');label.textContent=c.label;const value=document.createElement('b');value.textContent=c.result;div.append(label,value);return div;}));}catch{$('#verification').textContent='Отчёт сборки недоступен. Запустите npm test и CAD-проверки из README.';}}
loadVerification();refresh();
// Read-only diagnostics for browser smoke tests; mutations use visible controls.
globalThis.videosynth={getState:()=>structuredClone(state),getFrames:()=>frames,getLuma:()=>lastLuma?.slice(),getReady:()=>ready};
