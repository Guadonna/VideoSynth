import test from 'node:test';import assert from 'node:assert/strict';
import {VIDEO,raster,codeVoltage} from '../app/video.js';
const black=new Uint8Array(720*480);
test('exact 525/59.94 raster lengths, no progressive/30.000 substitution',()=>{assert.equal(VIDEO.frameSamples/VIDEO.sampleRate,1001/30000);assert.equal(VIDEO.fieldSamples/1716,262.5);assert.equal(VIDEO.frameSamples,900900);});
test('both fields have 6 pre-equalizing, 6 broad and 6 post-equalizing pulses',()=>{
 const r=raster(black);for(const f of [0,1])for(let half=0;half<18;half++){
  const start=f*450450+half*858,low=half>=6&&half<12?731:62;
  assert.ok(r.subarray(start,start+low).every(v=>v===0));assert.ok(r.subarray(start+low,start+858).every(v=>v===73));
 }
});
test('black output retains H sync; empty luma never enters sync level in active picture',()=>{const r=raster(black),start=22*1716;assert.ok(r.subarray(start,start+127).every(v=>v===0));assert.ok(r.subarray(start+244,start+1684).every(v=>v===73));});
test('field parity sends even and odd rows to distinct 262.5-line fields',()=>{const l=new Uint8Array(720*480);for(let y=1;y<480;y+=2)l.fill(255,y*720,(y+1)*720);const r=raster(l);assert.equal(r[44*858+244],73);assert.equal(r[570*858+244],255);assert.equal(r[1048*858+1683],255);});
test('2x interpolation and DAC loading have explicit numerical models',()=>{const l=black.slice();l[1]=255;const r=raster(l),base=44*858+244;assert.equal(r[base],73);assert.equal(r[base+1],164);assert.equal(r[base+2],255);assert.ok(Math.abs(codeVoltage(255)-1)<.002);assert.ok(Math.abs(codeVoltage(73)-.286)<.002);assert.equal(codeVoltage(0,true),.1425);});
test('non-native frames cannot be labelled as native composite',()=>assert.throws(()=>raster(new Uint8Array(320*240),320,240)));
