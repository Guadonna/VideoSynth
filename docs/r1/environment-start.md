# Start VideoSynth cloud environment

Use the existing checkout `/workspace/VideoSynth`; preserve user changes. Do not reset or regenerate routed PCB files merely to start the application.

1. Read README.md and docs/r1/validation.md. The image has Node.js, Chromium, KiCad 9 with `/usr/bin/python3` pcbnew, a C compiler, and libngspice. Project setup is `bash scripts/setup-cloud.sh`; it installs the pinned npm dependencies and a local checksum-verified wasi-sdk when absent. `WASI_CC` can override the compiler for manual builds.
2. Start `node scripts/serve.mjs` from the checkout, on port 4173. If that port is occupied, inspect the existing process before starting a duplicate. `PORT` may select another port.
3. Check `/app/index.html` and `/app/assets/engine.wasm` on the selected port. Use the cloud port preview UI. Do not claim that a localhost URL is externally accessible.
4. Run `npm test` for DSP/model/raster checks. Run `npm run test:browser` with the server active and `APP_URL` if using a nondefault port. `CHROMIUM` can select a different installed executable. For CAD/SPICE validation run `bash scripts/verify-hardware.sh`.
5. Export `XDG_CONFIG_HOME=/workspace/.config`, `XDG_CACHE_HOME=/workspace/.cache`, `XDG_DATA_HOME=/workspace/.local/share` before direct KiCad CLI calls in this read-only-home image.

The app needs no credentials or paid APIs. Never order fabrication or claim the electrical device is physically validated. The setup draft must be saved/published in environment settings to activate persistence; a fresh restored environment has not been independently tested.
