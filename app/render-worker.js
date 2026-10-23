// A classic Worker also works in browsers without support for module Workers.
// The standalone bundle embeds the runtime, so it needs no importScripts/fetch.
if (!globalThis.VideoSynthDSP) importScripts('./dsp-runtime.js');
const runtime = globalThis.VideoSynthDSP.createRuntime({emit: data => {
  const transfers = data.type === 'frame' ? [data.rgba.buffer, data.luma.buffer] : [];
  postMessage(data, transfers);
}});
self.onmessage = ({data}) => runtime.postMessage(data);
