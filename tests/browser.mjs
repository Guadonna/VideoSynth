import {chromium} from 'playwright';import assert from 'node:assert/strict';import {mkdir,writeFile,readFile} from 'node:fs/promises';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:1});const errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
const url=process.env.APP_URL||'http://127.0.0.1:4173/';
try{
 await page.goto(url);await page.waitForFunction(()=>window.videosynth?.getFrames()>3,null,{timeout:30000});for(const link of await page.locator('a[href$=".pdf"]').evaluateAll(nodes=>nodes.map(n=>n.href))){const response=await page.request.get(link);assert.equal(response.status(),200);assert.match(response.headers()['content-type'],/pdf/);}checks.push('browser loads WASM, renders native frame and resolves schematic PDFs');
 assert.equal(await page.locator('[data-param]').count(),24);assert.equal(await page.locator('.matrix-cell').count(),144);assert.equal(await page.locator('[data-toggle]').count(),6);
 await page.locator('#preset').selectOption('stress');await page.waitForFunction(()=>window.videosynth.getState().matrix.flat().filter(Boolean).length===36);
 await page.locator('.matrix-cell[data-x="17"][data-y="7"]').click();assert.equal(await page.locator('#route-count').textContent(),'36 / 36');assert.match(await page.locator('#toast').textContent(),/Лимит 36/);checks.push('37th route is rejected in UI');
 const before=await page.evaluate(()=>videosynth.getState().matrix);await page.locator('[data-toggle="1"]').click();assert.deepEqual(await page.evaluate(()=>videosynth.getState().matrix),before);checks.push('mix button leaves modulation intact');
 await page.locator('#mode').click();assert.equal(await page.locator('#slot').isDisabled(),true);assert.equal(await page.locator('#preview').isVisible(),true);await page.locator('#mode').click();checks.push('MODE changes LCD view; SLOT disabled in preview');
 await page.locator('#x-plus').click();assert.equal(await page.evaluate(()=>videosynth.getState().cursor.x),0); // 17 wraps to 0
 await page.locator('#y-plus').click();assert.equal(await page.evaluate(()=>videosynth.getState().cursor.y),0);
 await page.locator('#preset').selectOption('black');await page.waitForFunction(()=>videosynth.getLuma()?.every(v=>v===0),null,{timeout:15000});checks.push('black preset renders black pixels');
 await page.locator('#preset').selectOption('weave');await page.waitForFunction(()=>videosynth.getLuma()?.some(v=>v>200));
 const stateBefore=await page.evaluate(()=>videosynth.getState());await page.locator('#file').setInputFiles({name:'broken.json',mimeType:'application/json',buffer:Buffer.from('{"version":99}')});await page.waitForFunction(()=>document.querySelector('#toast').textContent.includes('отклонён'));assert.deepEqual(await page.evaluate(()=>videosynth.getState()),stateBefore);checks.push('invalid preset is rejected atomically');
 const downloadPromise=page.waitForEvent('download');await page.locator('#save').click();const download=await downloadPromise;assert.equal(download.suggestedFilename(),'VideoSynth-preset.json');checks.push('preset export downloads JSON');
 // Analytic pixel checks exercise the visible controls and the actual Worker.
 const samples=[[15,10],[60,10],[15,50],[60,50]];
 const wave=(f,p,n)=>Math.sin(2*Math.PI*f*p/n),code=v=>Math.round((v+1)*127.5);
 async function expectPixels(points){
  await page.waitForFunction(points=>{const a=videosynth.getLuma();return a&&points.every(([x,y,v])=>Math.abs(a[y*720+x]-v)<=1);},points,{timeout:15000});
  const canvas=await page.locator('#output').evaluate((c,points)=>{const a=c.getContext('2d').getImageData(0,0,720,480).data;return points.map(([x,y])=>a[(y*720+x)*4]);},points);
  points.forEach((p,i)=>assert.ok(Math.abs(canvas[i]-p[2])<=1));
 }
 await page.locator('#preset').selectOption('multiply');
 await expectPixels(samples.map(([x,y])=>[x,y,code(wave(8,x,720)*wave(6,y,480))]));
 await page.locator('[data-toggle="3"]').click();await expectPixels(samples.map(([x,y])=>[x,y,code(wave(8,x,720))]));
 await page.locator('[data-toggle="3"]').click();await page.locator('#osc-3-phase').fill('0.5');
 await expectPixels(samples.map(([x,y])=>[x,y,code(-wave(8,x,720)*wave(6,y,480))]));
 checks.push('mix controls multiply bipolar OSC, remove one factor and invert with phase');
 await page.locator('#preset').selectOption('am');const amPoints=[[15,30],[60,30],[15,150],[60,150]];
 await expectPixels(amPoints.map(([x,y])=>[x,y,code(wave(8,x,720)*wave(2,y,480))]));
 assert.equal(await page.locator('[data-toggle="3"]').getAttribute('aria-pressed'),'false');
 await page.screenshot({path:'docs/r1/screenshots/ring-am.png',fullPage:true});
 await page.locator('#slot').click();await expectPixels(amPoints.map(([x,y])=>[x,y,code(wave(8,x,720))]));
 checks.push('hidden V1 ring-AM inverts H1; disabling AM restores the unmodulated carrier');
 // Substitute DC CV for the OSC modulator, then check polarity and zero.
 await page.locator('.matrix-cell[data-x="1"][data-y="6"]').click();
 for(const volts of [10,-10,0]){
  await page.locator('[data-cv="0"][data-cv-param="volts"]').fill(String(volts));
  await expectPixels(amPoints.map(([x,y])=>[x,y,code(wave(8,x,720)*volts/10)]));
 }
 checks.push('CV through the AM slot preserves, inverts and suppresses the carrier');
 await page.locator('#preset').selectOption('multiply');
 await expectPixels(samples.map(([x,y])=>[x,y,code(wave(8,x,720)*wave(6,y,480))]));
 await page.locator('#mode').click();await page.screenshot({path:'docs/r1/screenshots/product-mix.png',fullPage:true});await page.locator('#mode').click();
 await page.locator('[data-tab="checks"]').click();await page.locator('#self-test').click();await page.waitForFunction(()=>document.querySelectorAll('#test-results .test-row').length===10);assert.equal(await page.locator('#test-results .fail').count(),0);checks.push('in-app self-test: 10 passed');
 await page.locator('[data-tab="instrument"]').click();await mkdir('docs/r1/screenshots',{recursive:true});await page.evaluate(()=>document.querySelector('#toast').style.visibility='hidden');await page.screenshot({path:'docs/r1/screenshots/emulator-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'docs/r1/screenshots/emulator-mobile.png',fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);checks.push('mobile viewport has no horizontal page overflow');
 // Standalone bundle: allow the initial HTML document, block all other HTTP traffic.
 const standalone=await browser.newPage({viewport:{width:1200,height:900}});standalone.on('pageerror',e=>errors.push(e.message));let external=0;
 await standalone.route('**/*',route=>{if(route.request().resourceType()==='document')route.continue();else{external++;route.abort();}});
 await standalone.goto(new URL('/dist/VideoSynth-R1.html',url).href);await standalone.waitForFunction(()=>window.videosynth?.getFrames()>2,null,{timeout:30000});assert.equal(external,0);checks.push('standalone HTML renders with zero external resource requests');
 await standalone.close();assert.deepEqual(errors,[]);const report={passed:checks.length,checks,pageErrors:errors,scope:'Chromium headless on host; not hardware timing or electrical validation'};await writeFile('hardware/verification/browser-summary.json',JSON.stringify(report,null,2)+'\n');console.log(report);
}finally{await browser.close();}
