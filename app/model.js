export const OSC_NAMES=['H1','H2','H3','V1','V2','V3'];
export const SOURCES=[...OSC_NAMES,'CV1','CV2'];
export const MODES=['FM','AM','PM'];
export const LIMIT=36;
export function initialState(){return {
 version:1,osc:OSC_NAMES.map((_,i)=>({frequency:8+4*(i%3),fine:0,phase:0,morph:0,mixed:i===0||i===3})),
 matrix:Array.from({length:8},()=>Array(18).fill(false)),cv:[0,1].map(()=>({mode:0,volts:0,frequency:1,amplitude:5})),
 cursor:{x:0,y:0},screen:'matrix'
};}
export function countRoutes(state){return state.matrix.flat().filter(Boolean).length;}
export function toggleRoute(state,y=state.cursor.y,x=state.cursor.x){
 if(!Number.isInteger(y)||y<0||y>=8||!Number.isInteger(x)||x<0||x>=18)return {ok:false,message:'Недопустимый слот'};
 if(!state.matrix[y][x]&&countRoutes(state)>=LIMIT)return {ok:false,message:'Лимит 36 связей'};
 state.matrix[y][x]=!state.matrix[y][x];return {ok:true};
}
export function moveCursor(state,dx,dy){state.cursor.x=(state.cursor.x+dx%18+18)%18;state.cursor.y=(state.cursor.y+dy%8+8)%8;}
export function slotButton(state){return state.screen==='matrix'?toggleRoute(state):{ok:false,message:'SLOT доступен в меню матрицы'};}
export function toggleOsc(state,i){if(Number.isInteger(i)&&i>=0&&i<6)state.osc[i].mixed=!state.osc[i].mixed;}
export function toggleScreen(state){state.screen=state.screen==='matrix'?'preview':'matrix';}
function number(v,lo,hi,label){if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)throw Error('Некорректное значение: '+label);return v;}
export function validateState(input){
 if(!input||input.version!==1||!Array.isArray(input.osc)||input.osc.length!==6)throw Error('Ожидается пресет VideoSynth версии 1');
 const s=initialState();
 s.osc=input.osc.map((o,i)=>{
  if(!o||typeof o.mixed!=='boolean')throw Error('Некорректное состояние OSC');
  return {frequency:number(o.frequency,.25,64,'frequency'),fine:number(o.fine,-1,1,'fine'),phase:number(o.phase,0,1,'phase'),morph:number(o.morph,0,3,'morph'),mixed:o.mixed};
 });
 if(!Array.isArray(input.matrix)||input.matrix.length!==8||input.matrix.some(r=>!Array.isArray(r)||r.length!==18||r.some(v=>typeof v!=='boolean')))throw Error('Матрица должна иметь размер 8×18');
 s.matrix=input.matrix.map(r=>[...r]);if(countRoutes(s)>36)throw Error('Пресет содержит больше 36 связей');
 if(!Array.isArray(input.cv)||input.cv.length!==2)throw Error('Нужны два CV-входа');
 s.cv=input.cv.map(c=>{if(c.mode!==0&&c.mode!==1)throw Error('Некорректный режим CV');return {mode:c.mode,volts:number(c.volts,-15,15,'CV volts'),frequency:number(c.frequency,0,100,'CV Hz'),amplitude:number(c.amplitude,0,10,'CV amplitude')};});
 if(input.cursor){s.cursor={x:number(input.cursor.x,0,17,'cursor X'),y:number(input.cursor.y,0,7,'cursor Y')};if(!Number.isInteger(s.cursor.x)||!Number.isInteger(s.cursor.y))throw Error('Курсор должен быть целым');}
 if(input.screen==='preview')s.screen='preview';return s;
}
export function preset(name){
 const s=initialState();
 if(name==='weave'){
  s.osc[0].frequency=11;s.osc[0].morph=3;s.osc[3].frequency=9;s.osc[3].morph=1;
  s.osc[1].frequency=3;s.osc[4].frequency=4;s.osc[1].morph=s.osc[4].morph=3;
  // Independent AM sources keep this demo out of a zero-start AM loop.
  for(const [y,x] of [[1,2],[4,11],[4,1],[1,10]])s.matrix[y][x]=true;
 }else if(name==='am'){
  s.osc.forEach((o,i)=>{o.mixed=i===0;o.frequency=i===3?2:8;});
  s.matrix[3][1]=true;s.cursor={x:1,y:3};
 }else if(name==='multiply'){
  s.osc[0].frequency=8;s.osc[3].frequency=6;
 }else if(name==='feedback'){
  s.osc.forEach((o,i)=>{o.mixed=i===0||i===3;o.frequency=[12,5,8,10,4,6][i];o.morph=.5;});
  for(const [y,x] of [[0,2],[3,0],[0,11],[3,9],[1,2],[4,11]])s.matrix[y][x]=true;
 }else if(name==='stress'){
  s.osc.forEach(o=>{o.mixed=true;o.morph=3;});
  // V3 supplies every AM bus, but has no AM input of its own. Closed
  // ring-AM loops started at zero otherwise produce a flat grey image.
  for(let y=0;y<6;y++)for(let target=0;target<6;target++){
   const mode=target===5?(y%2?2:0):y===5?1:(y+target)%3;
   s.matrix[y][target*3+mode]=true;
  }
 }else if(name==='black')s.osc.forEach(o=>o.mixed=false);
 return s;
}
export function cvModel(volts){
 const attenuation=100000/104700;
 const voltage=Math.min(3.3,Math.max(0,Math.min(5,Math.max(0,1.65-.12*volts))*attenuation));
 const code=Math.round(voltage/3.3*4095);
 return {voltage:code*3.3/4095,code,normalized:Math.max(-1,Math.min(1,(1.65-code*3.3/4095/attenuation)/1.2)),overload:Math.abs(volts)>10};
}
