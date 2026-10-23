import test from 'node:test';import assert from 'node:assert/strict';
import {initialState,countRoutes,toggleRoute,slotButton,toggleOsc,toggleScreen,moveCursor,validateState,preset,cvModel} from '../app/model.js';
test('144 addressable slots, 36 enabled including CV; 37th rejected atomically',()=>{
 const s=initialState();for(let i=0;i<36;i++)assert.equal(toggleRoute(s,Math.floor(i/18),i%18).ok,true);
 const before=structuredClone(s);assert.equal(toggleRoute(s,7,17).ok,false);assert.deepEqual(s,before);
 assert.equal(toggleRoute(s,0,0).ok,true);assert.equal(toggleRoute(s,7,17).ok,true);assert.equal(countRoutes(s),36);
});
test('oscillator buttons latch mix only and preserve modulation graph',()=>{const s=initialState();s.matrix[0][9]=true;toggleOsc(s,0);assert.equal(s.osc[0].mixed,false);assert.equal(s.matrix[0][9],true);toggleOsc(s,0);assert.equal(s.osc[0].mixed,true);});
test('MODE preserves parameters/routes; SLOT cannot change hidden matrix',()=>{const s=preset('weave'),osc=structuredClone(s.osc),matrix=structuredClone(s.matrix);toggleScreen(s);assert.equal(slotButton(s).ok,false);assert.deepEqual(s.matrix,matrix);assert.deepEqual(s.osc,osc);toggleScreen(s);assert.equal(s.screen,'matrix');});
test('two independent encoder axes wrap at 18 and 8',()=>{const s=initialState();moveCursor(s,-1,-1);assert.deepEqual(s.cursor,{x:17,y:7});moveCursor(s,1,1);assert.deepEqual(s.cursor,{x:0,y:0});});
test('import validates every numeric parameter and never exceeds DSP limits',()=>{
 for(const name of ['grid','weave','feedback','stress','black'])assert.deepEqual(validateState(preset(name)),preset(name));
 const s=initialState();s.matrix=Array.from({length:8},()=>Array(18).fill(true));assert.throws(()=>validateState(s),/36/);
 const bad=initialState();bad.osc[0].phase=NaN;assert.throws(()=>validateState(bad));bad.osc[0].phase=0;bad.cv[0].frequency=101;assert.throws(()=>validateState(bad));
});
test('CV DC model includes inverted gain, output load and ADC quantization',()=>{const hi=cvModel(10),lo=cvModel(-10);assert.ok(Math.abs(hi.voltage-.429799)<.001);assert.ok(Math.abs(lo.voltage-2.72206)<.001);assert.ok(hi.normalized>.999);assert.ok(lo.normalized<-.999);assert.equal(cvModel(15).overload,true);});
