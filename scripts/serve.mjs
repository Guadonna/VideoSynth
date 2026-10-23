import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const port=Number(process.env.PORT||4173);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.wasm':'application/wasm','.svg':'image/svg+xml','.png':'image/png','.pdf':'application/pdf'};
http.createServer(async(req,res)=>{
 try{
  let name=decodeURIComponent(new URL(req.url,'http://local').pathname);
  if(name==='/'){res.writeHead(302,{Location:'/app/index.html'});res.end();return;}
  if(name==='/app/')name='/app/index.html';
  const path=resolve(root,'.'+name);
  if(!path.startsWith(root+sep)||name.split('/').some(p=>p.startsWith('.'))){res.writeHead(403);res.end('Forbidden');return;}
  if(!(await stat(path)).isFile())throw Error('Not a file');
  res.setHeader('Content-Type',types[extname(path)]||'application/octet-stream');res.setHeader('Cache-Control','no-cache');res.end(await readFile(path));
 }catch{res.writeHead(404);res.end('Not found');}
}).listen(port,'0.0.0.0',()=>console.log(`VideoSynth server ready, port ${port}; /app/index.html`));
