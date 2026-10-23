import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const root=process.env.APP_URL||'http://127.0.0.1:4173/';
const checks=[],errors=[];
async function canvasIsLit(page,id){return page.locator('#'+id).evaluate(canvas=>{const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;return pixels.some((v,i)=>i%4<3&&v>180);});}
async function hashCanvas(page,id){return page.locator('#'+id).evaluate(canvas=>{let hash=2166136261;const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;for(const v of pixels)hash=Math.imul(hash^v,16777619);return hash>>>0;});}
async function ready(page){await page.waitForFunction(()=>window.videosynth?.getFrames()>2,null,{timeout:15000});assert.equal(await page.locator('#loading').isVisible(),false);assert.equal(await canvasIsLit(page,'output'),true);await page.locator('#mode').click();assert.equal(await canvasIsLit(page,'preview'),true);}
async function context(){const c=await browser.newContext({viewport:{width:1200,height:900}});c.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));return c;}
try{
 // Capture the Worker output for comparison with the SAME WASM under fallback.
 const normal=await context();const original=await normal.newPage();await original.goto(new URL('/app/index.html',root).href);await ready(original);await original.locator('#pause').click();const expected=await hashCanvas(original,'output');assert.equal(await original.evaluate(()=>videosynth.getDSPMode()),'worker');await normal.close();
 for(const path of ['/app/index.html','/dist/VideoSynth-R1.html']){
  const c=await context();let external=0;
  await c.route('**/*',async route=>{
   if(route.request().resourceType()==='document'){const response=await route.fetch();await route.fulfill({response,headers:{...response.headers(),'content-security-policy':"worker-src 'none'"}});}
   else if(path.includes('/dist/')){external++;await route.abort();}else await route.continue();
  });
  const p=await c.newPage();await p.goto(new URL(path,root).href);await ready(p);assert.equal(await p.evaluate(()=>videosynth.getDSPMode()),'main');await p.locator('#pause').click();assert.equal(await hashCanvas(p,'output'),expected);
  const before=await p.evaluate(()=>videosynth.getFrames());await p.locator('#osc-0-frequency').fill('27');await p.waitForFunction(n=>videosynth.getFrames()>n,before);assert.notEqual(await hashCanvas(p,'output'),expected);assert.equal(await canvasIsLit(p,'preview'),true);
  await p.locator('#preset').selectOption('black');await p.waitForFunction(()=>videosynth.getLuma().every(v=>v===0));await p.locator('#mode').click();assert.equal(await canvasIsLit(p,'output'),false);assert.equal(await canvasIsLit(p,'preview'),false);
  await p.locator('[data-toggle="0"]').click();await p.waitForFunction(()=>videosynth.getLuma().some(v=>v>200));assert.equal(await canvasIsLit(p,'preview'),true);
  const paused=await p.evaluate(()=>videosynth.getFrames());await p.waitForTimeout(150);assert.equal(await p.evaluate(()=>videosynth.getFrames()),paused);
  await p.locator('#pause').click();await p.waitForFunction(()=>videosynth.getFrames()>2);await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  if(path.includes('/dist/'))assert.equal(external,0);
  checks.push(`${path}: Worker blocked by CSP; both canvases render; WASM pixels match; paused edits and resume work${path.includes('/dist/')?'; no external resources':''}`);
  await p.screenshot({path:path.includes('/dist/')?'docs/r1/screenshots/dsp-compatibility-mobile.png':'docs/r1/screenshots/dsp-compatibility-server.png',fullPage:true});await c.close();
 }
 {
  const c=await context();await c.addInitScript(()=>{globalThis.Worker=undefined;});const p=await c.newPage();await p.goto(new URL('/dist/VideoSynth-R1.html',root).href);await ready(p);assert.equal(await p.evaluate(()=>videosynth.getDSPMode()),'main');checks.push('Missing Worker API: both canvases recover through main-thread WASM');await c.close();
 }
 {
  const c=await context();await c.addInitScript(()=>{globalThis.Worker=class{postMessage(){}terminate(){}};});const p=await c.newPage();await p.goto(new URL('/dist/VideoSynth-R1.html',root).href);
  await p.locator('#preset').selectOption('black');await p.locator('[data-toggle="0"]').click();await p.locator('#osc-0-frequency').fill('23');
  await ready(p);assert.equal(await p.evaluate(()=>videosynth.getState().osc[0].frequency),23);assert.equal(await p.evaluate(()=>videosynth.getDSPMode()),'main');checks.push('Worker startup timeout: recovery preserves controls changed during initialization');await c.close();
 }
 for(const failure of ['404','invalid']){
  const c=await context();await c.route('**/assets/engine.wasm',route=>route.fulfill({status:failure==='404'?404:200,contentType:'application/wasm',body:'not wasm'}));const p=await c.newPage();await p.goto(new URL('/app/index.html',root).href);
  await p.waitForFunction(()=>document.querySelector('#engine-metrics').textContent==='DSP недоступен');const message=await p.locator('#loading').textContent();assert.doesNotMatch(message,/undefined/);assert.equal(await p.evaluate(()=>videosynth.getReady()),false);assert.equal(await p.evaluate(()=>videosynth.getFrames()),0);
  if(failure==='404')assert.match(message,/HTTP 404/);else assert.match(message,/WebAssembly|magic|compile/i);checks.push(`WASM ${failure}: explicit failure message without undefined or stuck startup`);await c.close();
 }
 {
  const c=await context();let requests=0;await c.route('**/*',route=>{requests++;return route.abort();});const p=await c.newPage();await p.setContent(await readFile('dist/VideoSynth-R1.html','utf8'));await ready(p);assert.equal(requests,0);checks.push('Standalone HTML in an opaque-origin document renders without external resources');await c.close();
 }
 assert.deepEqual(errors,[]);const report={passed:checks.length,checks,pageErrors:errors,scope:'Chromium startup/fallback regression tests; file:// navigation remains blocked by cloud browser policy; no hardware validation'};
 await writeFile('hardware/verification/browser-compatibility-summary.json',JSON.stringify(report,null,2)+'\n');console.log(report);
}finally{await browser.close();}
