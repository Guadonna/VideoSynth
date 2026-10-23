import './dsp-runtime.js';

// Preserve controls if Worker creation/loading is denied by the browser.
export function createDSPClient({workerURL, onMessage, onStatus = () => {}, onError,
  loadBytes = globalThis.VideoSynthDSP.loadWasmBytes,
  workerFactory = url => new Worker(url), startupTimeoutMs = 5000}) {
  const {createRuntime, errorMessage} = globalThis.VideoSynthDSP;
  let backend, mode = 'worker', generation = 0, ready = false, disposed = false, timer;
  let latestState = null, running = true;
  function stopBackend() { clearTimeout(timer); backend?.terminate(); backend = null; ready = false; }
  function fatal(error) {
    if (disposed) return;
    generation++; stopBackend(); disposed = true;
    onError(errorMessage(error, 'DSP недоступен в этом браузере'));
  }
  function receive(data, id) {
    if (disposed || id !== generation) return;
    if (data.type === 'error') { if (mode === 'worker') fallback(data.message); else fatal(data.message); return; }
    if (data.type === 'ready') {
      clearTimeout(timer); ready = true;
      backend.postMessage({type: 'running', running});
      if (latestState) backend.postMessage({type: 'state', state: latestState});
    }
    onMessage(data);
  }
  function fallback(error) {
    if (disposed || mode === 'main') return;
    const id = ++generation; stopBackend(); mode = 'main';
    onStatus({mode, reason: errorMessage(error, 'Браузер не запустил фоновый Worker')});
    backend = createRuntime({loadBytes, emit: data => queueMicrotask(() => receive(data, id))});
    timer = setTimeout(() => fatal('Истекло время запуска DSP в совместимом режиме'), startupTimeoutMs * 2);
  }
  const client = {
    postMessage(data) {
      if (disposed) return;
      if (data.type === 'state') latestState = structuredClone(data.state);
      if (data.type === 'running') running = data.running;
      if (ready) backend.postMessage(data);
    },
    terminate() { disposed = true; generation++; stopBackend(); }
  };
  // Start after the caller has received the client, including synchronous failures.
  queueMicrotask(() => {
    if (disposed) return;
    const id = generation;
    try {
      backend = workerFactory(workerURL);
      backend.onmessage = ({data}) => receive(data, id);
      backend.onerror = error => {
        error.preventDefault?.();
        if (id === generation) fallback(error);
      };
      backend.onmessageerror = () => { if (id === generation) fallback('Ошибка передачи кадра из Worker'); };
      timer = setTimeout(() => fallback('Фоновый DSP не ответил при запуске'), startupTimeoutMs);
    } catch (error) { fallback(error); }
  });
  return client;
}
