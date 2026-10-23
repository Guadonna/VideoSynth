// 27 MHz, 1716 samples/line, 525 lines, 525 half-lines/field.
// Pulse widths rounded to samples: HSync 127, equalizing 62, serration 127.
export const VIDEO={sampleRate:27000000,lineSamples:1716,halfSamples:858,lines:525,frameSamples:900900,fieldSamples:450450,frameRate:30000/1001,fieldRate:60000/1001,black:73,white:255,sync:0};
export function raster(luma,width=720,height=480){
 if(!(luma instanceof Uint8Array)||width!==720||height!==480||luma.length!==width*height)throw Error('Для композитного растра нужен кадр 720×480');
 const out=new Uint8Array(VIDEO.frameSamples);out.fill(VIDEO.black);
 for(let half=0;half<1050;half++){
  const k=half%525,base=half*858;
  if(k<6||k>=12&&k<18)out.fill(0,base,base+62);
  else if(k>=6&&k<12)out.fill(0,base,base+731);
  else if(half%2===0)out.fill(0,base,base+127);
 }
 for(let f=0;f<2;f++)for(let row=0;row<240;row++){
  const y=2*row+f,base=((f?570:44)+2*row)*858+244;
  for(let x=0;x<720;x++){
   const a=luma[y*720+x],b=luma[y*720+Math.min(x+1,719)];
   out[base+2*x]=73+Math.round(182*a/255);
   out[base+2*x+1]=73+Math.round(182*(a+b)/510);
  }
 }
 return out;
}
export function codeVoltage(code,absolute=false){
 const full=(32*1.2/1910)*49.9;
 return full*code/256+(absolute?.1425:0);
}
