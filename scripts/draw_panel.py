"""Provisional panel layout from physical shaft offsets; not a manufacturing drawing."""
from pathlib import Path
import csv
out=Path(__file__).resolve().parents[1]/'hardware/panel';out.mkdir(exist_ok=True)
ox,oy=2.54,10.25;holes=[]
for i in range(6):
 for j in range(4):holes.append((f'{["H1","H2","H3","V1","V2","V3"][i]} { ["FREQ","FINE","PHASE","MORPH"][j]}',ox+12+22*i,oy+16+20*j,7.2,'pot candidate'))
for i in range(6):holes.append((f'OSC{i+1}',ox+12+22*i,oy+94,4.0,'actuator opening provisional'))
for i in range(6):holes.append((f'LED{i+1}',ox+19+22*i,oy+94,2.0,'lightpipe opening provisional'))
for name,x in [('ENC X',155),('ENC Y',183)]:holes.append((name,ox+x+7.5,oy+62+2.5,7.2,'EC11 shaft offset +7.5/+2.5 from footprint'))
for name,x in [('MODE',156),('SLOT',184)]:holes.append((name,ox+x,oy+82,4.0,'actuator opening provisional'))
for name,x in [('CV1',153),('CV2',177)]:holes.append((name,ox+x,oy+96.48,6.4,'PJ398SM shaft offset +0/+6.48'))
holes.append(('OUT',ox+199,oy+96.48,8,'RCA candidate diameter only'))
s=['<svg xmlns="http://www.w3.org/2000/svg" width="213.06mm" height="128.5mm" viewBox="0 0 213.06 128.5">','<rect x=".1" y=".1" width="212.86" height="128.3" rx="1" fill="#e5e3d7" stroke="#333" stroke-width=".2"/>','<g font-family="monospace" text-anchor="middle" fill="#263032">','<text x="106.53" y="8" font-size="4">VIDEOSYNTH R1 · 42 HP</text>','<text x="106.53" y="122" font-size="2.1">PROVISIONAL · CHECK ACTUAL PARTS / HEIGHTS BEFORE CUTTING</text>']
for x in [7.5,205.62]:
 for y in [3,125.5]:s.append(f'<rect x="{x-3.5}" y="{y-1.6}" width="7" height="3.2" rx="1.6" fill="none" stroke="#aa4433" stroke-width=".25"/>')
for label,x,y,d,note in holes:
 s.append(f'<circle cx="{x}" cy="{y}" r="{d/2}" fill="none" stroke="#333" stroke-width=".25"/>')
 if not label.startswith('LED'):s.append(f'<text x="{x}" y="{y-d/2-1.8}" font-size="1.9">{label}</text>')
s+=['<rect x="147" y="23" width="50.5" height="38.5" fill="#263638" stroke="#aa4433" stroke-width=".3" stroke-dasharray="1 1"/>','<text x="172.25" y="42" font-size="3" fill="#b8d3cf">TFT 320 × 240</text>','<text x="172.25" y="47" font-size="1.7" fill="#b8d3cf">WINDOW TO BE CONFIRMED</text>','</g></svg>']
(out/'front-panel-provisional.svg').write_text('\n'.join(s))
with (out/'opening-centres-provisional.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['name','panel_x_mm','panel_y_mm','candidate_diameter_mm','note']);w.writerows(holes)
