# Portable DSP reference

`dsp/engine.c` is the shared C implementation used by native tests and the browser WebAssembly build. It contains no ESP-IDF target, GPIO, PARLIO, DMA or board drivers. It is not flashable firmware.

Build the browser artifact with `python3 scripts/build.py` (wasi-sdk 25 or `WASI_CC`). Run the native and WASM tests with `npm test`. The browser always requests 720×480. Reduced sizes in the C API exist for focused tests.

The reference uses static buffers and is not thread-safe; do not call it concurrently from multiple tasks. A hardware implementation needs explicit per-task state/buffer ownership and measured scheduling. See [DSP semantics](../docs/r1/dsp.md) and [bring-up gates](../docs/r1/bringup.md).
