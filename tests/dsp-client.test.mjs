import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createDSPClient} from '../app/dsp-client.js';
import {preset} from '../app/model.js';
const bytes=await readFile(new URL('../app/assets/engine.wasm',import.meta.url));
const {createRuntime,errorMessage}=globalThis.VideoSynthDSP;
function probe(){
 const messages=[],waiters=[];
 return {messages,emit(data){messages.push(data);for(const w of [...waiters])if(w.match(data)){clearTimeout(w.timer);waiters.splice(waiters.indexOf(w),1);w.resolve(data);}},
  next(match){const existing=messages.find(match);if(existing)return Promise.resolve(existing);return new Promise((resolve,reject)=>{const w={match,resolve,timer:setTimeout(()=>reject(Error('No expected DSP event')),5000)};waiters.push(w);});}};
}
function setup(t,workerFactory,extra={}){
 const output=probe(),statuses=[],errors=[];
 const client=createDSPClient({workerURL:'unused',workerFactory,loadBytes:()=>bytes,onMessage:d=>output.emit(d),onStatus:s=>statuses.push(s),onError:message=>{errors.push(message);output.emit({type:'fatal',message});},...extra});
 t.after(()=>client.terminate());return {client,output,statuses,errors};
}
test('runtime accepts state and pause before WASM finishes loading',async t=>{
 let resolveBytes;const output=probe();const runtime=createRuntime({loadBytes:()=>new Promise(resolve=>{resolveBytes=resolve;}),emit:d=>output.emit(d)});t.after(()=>runtime.terminate());
 runtime.postMessage({type:'running',running:false});runtime.postMessage({type:'state',state:preset('black')});resolveBytes(bytes);
 const frame=await output.next(d=>d.type==='frame');assert.equal(frame.frame,0);assert.equal(frame.luma.length,345600);assert.ok(frame.luma.every(v=>v===0));assert.equal(output.messages.filter(d=>d.type==='error').length,0);
});
test('a synchronous Worker rejection falls back and preserves paused controls',async t=>{
 const {client,output,statuses,errors}=setup(t,()=>{throw new DOMException('Worker blocked','SecurityError');});
 client.postMessage({type:'running',running:false});client.postMessage({type:'state',state:preset('black')});
 const first=await output.next(d=>d.type==='frame');assert.ok(first.luma.every(v=>v===0));assert.equal(statuses[0].mode,'main');assert.deepEqual(errors,[]);
 client.postMessage({type:'state',state:preset('weave')});const second=await output.next(d=>d.type==='frame'&&d.frame>0);assert.ok(second.luma.some(v=>v>200));assert.equal(second.frame,1);
});
test('an error Event without message recovers; stale Worker events are ignored',async t=>{
 let old;const {client,output,statuses,errors}=setup(t,()=>{old={postMessage(){},terminate(){this.stopped=true;}};setTimeout(()=>old.onerror(new Event('error',{cancelable:true})),0);return old;});
 client.postMessage({type:'state',state:preset('weave')});client.postMessage({type:'running',running:false});
 await output.next(d=>d.type==='frame');assert.equal(old.stopped,true);assert.doesNotMatch(statuses[0].reason,/undefined/);const count=output.messages.length;
 old.onmessage({data:{type:'error',message:'late failure'}});old.onmessage({data:{type:'ready'}});assert.equal(output.messages.length,count);assert.deepEqual(errors,[]);
});
test('a Worker that never becomes ready times out into the same WASM renderer',async t=>{
 const {client,output,statuses}=setup(t,()=>({postMessage(){},terminate(){}}),{startupTimeoutMs:250});client.postMessage({type:'state',state:preset('weave')});client.postMessage({type:'running',running:false});
 const frame=await output.next(d=>d.type==='frame');assert.ok(frame.luma.some(v=>v>200));assert.match(statuses[0].reason,/не ответил/);
});
test('a missing WASM asset produces one actionable error, not undefined',async t=>{
 const {output,errors}=setup(t,()=>{throw Error('Worker denied');},{loadBytes:()=>{throw Error('Не удалось загрузить engine.wasm: HTTP 404');}});
 const error=await output.next(d=>d.type==='fatal');assert.match(error.message,/HTTP 404/);assert.deepEqual(errors,[error.message]);assert.equal(output.messages.filter(d=>d.type==='ready').length,0);
});
test('terminating during WASM loading cannot revive the renderer',async()=>{
 let finish;const output=probe();const runtime=createRuntime({loadBytes:()=>new Promise(resolve=>{finish=resolve;}),emit:d=>output.emit(d)});
 runtime.terminate();finish(bytes);await new Promise(resolve=>setImmediate(resolve));assert.deepEqual(output.messages,[]);
 assert.equal(errorMessage(new Event('error'),'Worker unavailable'),'Worker unavailable');assert.equal(errorMessage(undefined,'Worker unavailable'),'Worker unavailable');
});
