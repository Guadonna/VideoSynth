# VideoSynth R1 hardware

Open `kicad/core/videosynth_core.kicad_pro` and `kicad/panel/videosynth_panel.kicad_pro` in KiCad 9. Both projects include editable schematics, routed four-layer PCBs and local symbol libraries. PDFs are `core-schematic.pdf` and `panel-schematic.pdf` in the respective folders. The two boards use separate reference-designator namespaces.

`design.json` / `tools/design.py` describe electrical connectivity and initial placement. `bom-r1.csv` lists physical parts; blank MPNs and candidates still require procurement qualification. `external-assemblies.csv` includes module, display and harnesses beyond the PCB BOM. Front-panel drawing in `panel/` is provisional.

Verification: `bash scripts/verify-hardware.sh` from the repository root. It exports schematics/netlists, runs ERC/DRC, compares all PCB pads to the manifest and runs linear CV SPICE. It does not regenerate the PCB.

**Do not run `tools/build_kicad.py` without `--schematics-only` on the finished layout: full regeneration intentionally replaces routed boards.** Router helper scripts are development tools, not a production automation pipeline.

R1 is a testable prototype design, not a manufacturing release. Mandatory module FET2 removal, power harness wiring, unqualified component substitutions, analog/timing risks and mechanical gaps are documented in [hardware.md](../docs/r1/hardware.md). No production order has been placed.
