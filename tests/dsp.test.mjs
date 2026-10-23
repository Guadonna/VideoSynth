import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {preset} from '../app/model.js';
const bytes=await readFile(new URL('../app/assets/engine.wasm',import.meta.url));
async function engine(){const e=(await WebAssembly.instantiate(bytes,{})).instance.exports;e.reset_state();return e;}
function luma(e){return new Uint8Array(e.memory.buffer,e.luma_ptr(),e.get_width()*e.get_height()).slice();}
function osc(e,i,{f=8,fine=0,phase=0,morph=0,mix=0}={}){assert.equal(e.set_osc(i,f,fine,phase,morph,mix),0);}
test('native 720×480 is computed, with black only when mix is empty',async()=>{const e=await engine();for(let i=0;i<6;i++)osc(e,i);assert.equal(e.render_frame(0),345600);assert.ok(luma(e).every(x=>x===0));osc(e,0,{mix:1});e.render_frame(0);assert.ok(luma(e).some(x=>x>200));});
test('unmodulated H follows X, V follows Y across both interlaced fields',async()=>{
 const e=await engine();for(let i=0;i<6;i++)osc(e,i);e.set_size(64,48);osc(e,0,{f:2,mix:1});e.render_frame(0);let a=luma(e);assert.equal(a[0],128);assert.equal(a[8],255);assert.deepEqual(a.slice(0,64),a.slice(64,128));
 osc(e,0);osc(e,3,{f:2,mix:1});e.render_frame(0);a=luma(e);assert.equal(a[6*64],255);for(let y=0;y<48;y++)assert.ok(a.slice(y*64,(y+1)*64).every(v=>v===a[y*64]));
});
test('an oscillator excluded from mix remains an effective modulator',async()=>{const e=await engine();e.set_size(64,48);for(let i=0;i<6;i++)osc(e,i);osc(e,0,{mix:1});osc(e,1,{f:3});e.render_frame(0);const a=luma(e);e.set_route(1,2,1);e.render_frame(0);const b=luma(e);assert.notDeepEqual(b,a);osc(e,1,{f:3,mix:0});e.render_frame(0);assert.deepEqual(luma(e),b);});
test('cyclic cross-modulation, self-PM and all 36 routes are deterministic',async()=>{const e=await engine();const s=preset('stress');for(let y=0;y<8;y++)for(let d=0;d<18;d++)if(s.matrix[y][d])assert.equal(e.set_route(y,d,1),0);assert.equal(e.route_count(),36);assert.equal(e.set_route(7,17,1),-2);assert.equal(e.route_count(),36);e.render_frame(0);const a=luma(e);e.render_frame(0);assert.deepEqual(luma(e),a);assert.ok(a.some(v=>v!==a[0]));});
test('DC CV changes render through the matrix; LFO preserves deterministic simulated time',async()=>{const e=await engine();e.set_size(64,48);e.set_route(6,2,1);e.set_cv(0,0,0,1,5);e.render_frame(0);const a=luma(e);e.set_cv(0,0,5,1,5);e.render_frame(0);assert.notDeepEqual(luma(e),a);e.set_cv(0,1,0,2,5);e.render_frame(.125);const b=luma(e);e.render_frame(.125);assert.deepEqual(luma(e),b);e.render_frame(.375);assert.notDeepEqual(luma(e),b);});
test('invalid inputs, including NaN, are rejected without corrupting state',async()=>{const e=await engine();assert.equal(e.set_osc(0,NaN,0,0,0,1),-1);assert.equal(e.set_route(-1,0,1),-1);assert.equal(e.set_route(8,0,1),-1);assert.equal(e.set_route(0,18,1),-1);assert.equal(e.set_size(721,480),-1);assert.equal(e.set_size(720,479),-1);assert.equal(e.set_cv(0,1,0,101,5),-1);assert.equal(e.render_frame(NaN),-1);assert.equal(e.render_frame(0),345600);});

const code=x=>Math.round((Math.max(-1,Math.min(1,x))+1)*127.5);
function near(actual,expected){assert.ok(Math.abs(actual-expected)<=1,`luma ${actual}, expected ${expected} ±1 LSB`);}
async function isolated(){const e=await engine();e.set_size(64,48);for(let i=0;i<6;i++)osc(e,i,{f:2});return e;}
test('mix multiplies bipolar signals: identical waves square, opposite waves invert the product',async()=>{
 const e=await isolated();osc(e,0,{f:2,mix:1});e.render_frame(0);const single=luma(e);
 osc(e,1,{f:2,mix:1});e.render_frame(0);const squared=luma(e);
 for(let x=0;x<64;x++)near(squared[x],code(Math.sin(2*Math.PI*2*x/64)**2));
 assert.notDeepEqual(squared,single);assert.equal(single[24],0);assert.equal(squared[24],255);
 osc(e,1,{f:2,phase:.5,mix:1});e.render_frame(0);const inverted=luma(e);
 for(let x=0;x<64;x++)near(inverted[x],code(-(Math.sin(2*Math.PI*2*x/64)**2)));
 assert.equal(inverted[24],0);assert.equal(inverted[0],128);
});
test('all six selected OSC form one product; disabling a factor leaves the product of the rest',async()=>{
 const e=await isolated();for(let i=0;i<6;i++)osc(e,i,{f:2,phase:i/12,mix:1});
 for(const active of [6,5,1,0]){
  for(let i=0;i<6;i++)osc(e,i,{f:2,phase:i/12,mix:i<active?1:0});e.render_frame(0);const a=luma(e);
  for(const y of [2,3,6,11,18])for(const x of [2,8,13,24]){
   let product=1;for(let i=0;i<active;i++)product*=Math.sin(2*Math.PI*(2*(i<3?x/64:y/48)+i/12));
   near(a[y*64+x],active?code(product):0);
  }
 }
});
test('ring AM: +10 V preserves, -10 V inverts, 0 V removes the carrier; disabling restores it',async()=>{
 const e=await isolated();osc(e,0,{f:2,mix:1});e.render_frame(0);const original=luma(e);e.set_route(6,1,1);
 for(const volts of [10,0,-10]){
  e.set_cv(0,0,volts,1,5);e.render_frame(0);const a=luma(e);
  const gain=volts/10;
  for(let x=0;x<64;x++)near(a[x],code(Math.sin(2*Math.PI*2*x/64)*gain));
  if(volts===0)assert.ok(a.every(v=>v===127||v===128));
 }
 e.set_route(6,1,0);e.render_frame(0);assert.deepEqual(luma(e),original);
});
test('invisible OSC ring-modulates with previous-active-pixel latency, in both fields',async()=>{
 const e=await isolated();osc(e,0,{f:2,mix:1});osc(e,3,{f:2});e.set_route(3,1,1);e.render_frame(0);const a=luma(e);
 for(let y=0;y<48;y++)for(let x=1;x<64;x++)near(a[y*64+x],code(Math.sin(2*Math.PI*2*x/64)*Math.sin(2*Math.PI*2*y/48)));
 // Row starts read the preceding active line, not a value from the future.
 osc(e,0,{f:2,phase:.25,mix:1});e.render_frame(0);const b=luma(e);
 assert.equal(b[0],128);assert.equal(b[64],128);
 for(let y=2;y<48;y++)near(b[y*64],code(Math.sin(2*Math.PI*2*(y-2)/48)));
 assert.equal(a[6*64+8],255);assert.equal(a[18*64+8],0);
});
test('several AM controls add on a bipolar bus, cancel and clip without a carrier bias',async()=>{
 const e=await isolated();osc(e,0,{f:2,mix:1});e.set_route(6,1,1);e.set_route(7,1,1);
 for(const [a,b,gain] of [[10,-10,0],[10,10,1],[-10,-10,-1]]){
  e.set_cv(0,0,a,1,5);e.set_cv(1,0,b,1,5);e.render_frame(0);const frame=luma(e);
  for(let x=0;x<64;x++)near(frame[x],code(gain*Math.sin(2*Math.PI*2*x/64)));
 }
});
test('a closed AM-only feedback loop with zero history stays at zero; bypass breaks the loop',async()=>{
 const e=await isolated();osc(e,0,{f:2,mix:1});osc(e,1,{f:3});e.set_route(1,1,1);e.set_route(0,4,1);e.render_frame(0);
 assert.ok(luma(e).every(v=>v===128));e.set_route(0,4,0);e.render_frame(0);assert.ok(luma(e).some(v=>v<64));
});
test('AM and product demo presets and the revised weave produce non-flat images',async()=>{
 for(const name of ['am','multiply','weave','stress']){
  const e=await engine(),s=preset(name);
  for(let i=0;i<6;i++){const o=s.osc[i];osc(e,i,{f:o.frequency,fine:o.fine,phase:o.phase,morph:o.morph,mix:o.mixed?1:0});}
  for(let y=0;y<8;y++)for(let x=0;x<18;x++)if(s.matrix[y][x])e.set_route(y,x,1);
  e.render_frame(0);const frame=luma(e);assert.ok(frame.some(v=>v<120),name);assert.ok(frame.some(v=>v>136),name);
 }
});
