// Shared by a classic Worker and the main-thread compatibility renderer.
// Keep this file free of module syntax so importScripts() can load it too.
globalThis.VideoSynthDSP = (() => {
  function errorMessage(error, fallback = 'Браузер не сообщил причину ошибки') {
    if (typeof error === 'string' && error.trim()) return error;
    if (typeof error?.message === 'string' && error.message.trim()) return error.message;
    return fallback;
  }

  async function loadWasmBytes() {
    if (typeof WebAssembly === 'undefined') throw Error('В этом браузере недоступен WebAssembly');
    if (globalThis.WASM_BASE64) return Uint8Array.from(atob(globalThis.WASM_BASE64), c => c.charCodeAt(0));
    const response = await fetch('./assets/engine.wasm');
    if (!response.ok) throw Error(`Не удалось загрузить engine.wasm: HTTP ${response.status}`);
    return response.arrayBuffer();
  }

  function createRuntime({loadBytes = loadWasmBytes, emit}) {
    let api, state = null, running = true, frame = 0, timer = null, stopped = false;
    function terminate() { stopped = true; clearTimeout(timer); }
    function fail(error) { terminate(); emit({type: 'error', message: errorMessage(error)}); }
    function apply() {
      api.clear_routes();
      for (let i = 0; i < 6; i++) {
        const o = state.osc[i];
        if (api.set_osc(i, o.frequency, o.fine, o.phase, o.morph, +o.mixed)) throw Error('Invalid OSC');
      }
      for (let y = 0; y < 8; y++) for (let x = 0; x < 18; x++) {
        if (state.matrix[y][x] && api.set_route(y, x, 1)) throw Error('Route limit');
      }
      for (let i = 0; i < 2; i++) {
        const c = state.cv[i];
        if (api.set_cv(i, c.mode, c.volts, c.frequency, c.amplitude)) throw Error('Invalid CV');
      }
    }
    function draw() {
      if (!state || !api || stopped) return;
      const started = performance.now();
      if (api.render_frame(frame * 1001 / 30000) !== 720 * 480) throw Error('DSP не сформировал полный кадр');
      const rgba = new Uint8ClampedArray(api.memory.buffer, api.pixels_ptr(), 720 * 480 * 4).slice();
      const luma = new Uint8Array(api.memory.buffer, api.luma_ptr(), 720 * 480).slice();
      emit({type: 'frame', rgba, luma, renderMs: performance.now() - started, frame, simTime: frame * 1001 / 30000});
      frame++;
    }
    function loop() {
      if (stopped || !running || !api) return;
      const started = performance.now();
      try { draw(); } catch (error) { fail(error); return; }
      // Yield to input/painting even when the host cannot render in 33.37 ms.
      if (!stopped && running) timer = setTimeout(loop, Math.max(8, 1001 / 30 - (performance.now() - started)));
    }
    function postMessage(data) {
      if (stopped) return;
      try {
        if (data.type === 'state') {
          state = structuredClone(data.state);
          if (api) { apply(); if (!running) draw(); }
        } else if (data.type === 'running') {
          running = data.running; clearTimeout(timer);
          if (running && api) timer = setTimeout(loop, 0);
        } else if (data.type === 'resetTime') {
          frame = 0; if (!running) draw();
        }
      } catch (error) { fail(error); }
    }
    async function boot() {
      try {
        const bytes = await loadBytes();
        if (stopped) return;
        api = (await WebAssembly.instantiate(bytes, {})).instance.exports;
        if (stopped) return;
        api.reset_state(); if (state) apply();
        emit({type: 'ready'});
        if (running) timer = setTimeout(loop, 0); else draw();
      } catch (error) { if (!stopped) fail(error); }
    }
    void boot();
    return {postMessage, terminate};
  }
  return {createRuntime, loadWasmBytes, errorMessage};
})();
