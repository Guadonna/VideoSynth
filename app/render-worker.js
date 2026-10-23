let api,state=null,running=true,last=0,frame=0,timer;
const source=globalThis.WASM_BASE64?Uint8Array.from(atob(globalThis.WASM_BASE64),c=>c.charCodeAt(0)):await (await fetch('./assets/engine.wasm')).arrayBuffer();
try{
 api=(await WebAssembly.instantiate(source,{})).instance.exports;api.reset_state();postMessage({type:'ready'});
}catch(error){postMessage({type:'error',message:String(error)});throw error;}
function apply(s){
 api.clear_routes();
 for(let i=0;i<6;i++){const o=s.osc[i];if(api.set_osc(i,o.frequency,o.fine,o.phase,o.morph,+o.mixed))throw Error('Invalid OSC');}
 for(let y=0;y<8;y++)for(let x=0;x<18;x++)if(s.matrix[y][x]&&api.set_route(y,x,1))throw Error('Route limit');
 for(let i=0;i<2;i++){const c=s.cv[i];if(api.set_cv(i,c.mode,c.volts,c.frequency,c.amplitude))throw Error('Invalid CV');}
}
self.onmessage=({data})=>{
 if(data.type==='state'){state=data.state;apply(state);if(!running)draw();}
 if(data.type==='running'){running=data.running;clearTimeout(timer);if(running)loop();}
 if(data.type==='resetTime'){frame=0;if(!running)draw();}
};
function draw(){
 if(!state)return;
 const started=performance.now();api.render_frame(frame*1001/30000);
 const rgba=new Uint8ClampedArray(api.memory.buffer,api.pixels_ptr(),720*480*4).slice();
 const luma=new Uint8Array(api.memory.buffer,api.luma_ptr(),720*480).slice();
 const elapsed=performance.now()-started;
 postMessage({type:'frame',rgba,luma,renderMs:elapsed,frame,simTime:frame*1001/30000},[rgba.buffer,luma.buffer]);frame++;
}
function loop(){const started=performance.now();draw();if(running)timer=setTimeout(loop,Math.max(0,1001/30-(performance.now()-started)));}
loop();
