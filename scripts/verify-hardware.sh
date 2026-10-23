#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/workspace/.config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/workspace/.cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/workspace/.local/share}"
for board_name in core panel; do
  project="hardware/kicad/$board_name/videosynth_$board_name"
  kicad-cli sch erc -o "hardware/verification/$board_name-erc.txt" "$project.kicad_sch"
  kicad-cli sch export netlist --format kicadxml -o "hardware/verification/$board_name-netlist.xml" "$project.kicad_sch"
  kicad-cli sch export pdf -o "hardware/kicad/$board_name/$board_name-schematic.pdf" "$project.kicad_sch"
  kicad-cli pcb drc --format json -o "hardware/verification/$board_name-drc.json" "$project.kicad_pcb"
  kicad-cli pcb export svg --layers F.Cu,F.Fab,F.Silkscreen,Edge.Cuts,Dwgs.User --mode-single --page-size-mode 2 --exclude-drawing-sheet -o "app/assets/$board_name-board.svg" "$project.kicad_pcb"
done
/usr/bin/python3 hardware/tools/verify_connectivity.py
python3 hardware/simulation/run_spice.py
python3 scripts/r1_summary.py
