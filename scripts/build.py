#!/usr/bin/env python3
"""Build browser WASM with pinned local wasi-sdk, without network access."""
import os,subprocess,pathlib,hashlib,json
root=pathlib.Path(__file__).resolve().parents[1]
cc=os.environ.get('WASI_CC','/workspace/tools/wasi-sdk-25.0-x86_64-linux/bin/clang')
cmd=[cc,'--target=wasm32','-O3','-fno-builtin','-nostdlib','-Wl,--no-entry','-Wl,--export-all','-Wl,--initial-memory=4194304','-Wl,--max-memory=16777216',str(root/'firmware/dsp/engine.c'),'-o',str(root/'app/assets/engine.wasm')]
subprocess.run(cmd,check=True)
p=root/'app/assets/engine.wasm';print(p.name,p.stat().st_size,'bytes',hashlib.sha256(p.read_bytes()).hexdigest())
