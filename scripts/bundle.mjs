// Standalone HTML: all assets are local/embedded; no server or CDN required.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const r=p=>readFile(new URL('../'+p,import.meta.url),'utf8');
const base64=(await readFile(new URL('../app/assets/engine.wasm',import.meta.url))).toString('base64');
const runtime=await r('app/dsp-runtime.js');
const worker=`globalThis.WASM_BASE64=${JSON.stringify(base64)};\n`+runtime+'\n'+await r('app/render-worker.js');
let script=runtime+'\n'+(await r('app/dsp-client.js')).replace(/^import .*;\n/gm,'').replace(/^export /gm,'')+'\n'+(await r('app/model.js')).replace(/^export /gm,'')+'\n'+(await r('app/video.js')).replace(/^export /gm,'')+'\n'+(await r('app/main.js')).replace(/^import .*;\n/gm,'').replace("new URL('./render-worker.js',import.meta.url)","''");
let verification={checks:[]};try{verification=JSON.parse(await r('app/assets/verification.json'));}catch{}
script=`globalThis.WASM_BASE64=${JSON.stringify(base64)};globalThis.EMBEDDED_WORKER=${JSON.stringify(worker)};globalThis.VERIFICATION=${JSON.stringify(verification)};\n`+script;
const css=await r('app/style.css');let html=await r('app/index.html');html=html.replace('<link rel="stylesheet" href="./style.css">',()=>`<style>${css}</style>`).replace('<script type="module" src="./main.js"></script>',()=>`<script type="module">${script.replace(/<\/script/gi,'<\\/script')}</script>`);
for(const name of ['core','panel']){try{const svg=await r(`app/assets/${name}-board.svg`);html=html.replace(`src="./assets/${name}-board.svg"`,`src="data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}"`);}catch{}}
// PDFs live beside source files in the repository, not inside an HTML blob.
html=html.replaceAll('href="../hardware/','href="https://github.com/Guadonna/VideoSynth/blob/main/hardware/');
await mkdir(new URL('../dist/',import.meta.url),{recursive:true});await writeFile(new URL('../dist/VideoSynth-R1.html',import.meta.url),html);console.log('Standalone HTML:',Buffer.byteLength(html),'bytes');
