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
 await page.locator('[data-tab="checks"]').click();await page.locator('#self-test').click();await page.waitForFunction(()=>document.querySelectorAll('#test-results .test-row').length===7);assert.equal(await page.locator('#test-results .fail').count(),0);checks.push('in-app self-test: 7 passed');
 await page.locator('[data-tab="instrument"]').click();await mkdir('docs/r1/screenshots',{recursive:true});await page.evaluate(()=>document.querySelector('#toast').style.visibility='hidden');await page.screenshot({path:'docs/r1/screenshots/emulator-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'docs/r1/screenshots/emulator-mobile.png',fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);checks.push('mobile viewport has no horizontal page overflow');
 // Standalone bundle: allow the initial HTML document, block all other HTTP traffic.
 const standalone=await browser.newPage({viewport:{width:1200,height:900}});standalone.on('pageerror',e=>errors.push(e.message));let external=0;
 await standalone.route('**/*',route=>{if(route.request().resourceType()==='document')route.continue();else{external++;route.abort();}});
 await standalone.goto(new URL('/dist/VideoSynth-R1.html',url).href);await standalone.waitForFunction(()=>window.videosynth?.getFrames()>2,null,{timeout:30000});assert.equal(external,0);checks.push('standalone HTML renders with zero external resource requests');
 await standalone.close();assert.deepEqual(errors,[]);const report={passed:checks.length,checks,pageErrors:errors,scope:'Chromium headless on host; not hardware timing or electrical validation'};await writeFile('hardware/verification/browser-summary.json',JSON.stringify(report,null,2)+'\n');console.log(report);
}finally{await browser.close();}
