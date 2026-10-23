#!/usr/bin/python3
"""Generate editable KiCad 9 projects from design.py, with deterministic UUIDs.
WARNING: regenerating a board replaces routing. Use --schematics-only to preserve it.
"""
import sys, os, json, math, re
from pathlib import Path
import uuid
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
os.environ.setdefault('XDG_CACHE_HOME','/workspace/.cache')
os.environ.setdefault('XDG_DATA_HOME','/workspace/.local/share')
import pcbnew as pcb
from design import PARTS,BOARD_CONFIG,ROOT,dump
NS=uuid.UUID('2d6dc5c5-5040-4338-a5c1-8b0639c96bcc')
def uid(s):return str(uuid.uuid5(NS,s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def effect(sz=1,hide=False):return f'(effects (font (size {sz} {sz}))'+(' (hide yes)' if hide else '')+')'
def point(x,y):return pcb.VECTOR2I(round(x*1e6),round(y*1e6))

def geom(p):
 pins=list(p['pins']); n=(len(pins)+1)//2
 if len(pins)==1:return [('1',-12.7,0,0)],4
 if len(pins)==2:return [(pins[0],-5.08,0,0),(pins[1],5.08,0,180)],2.54
 out=[]
 for i,num in enumerate(pins):
  left=i<n;k=i if left else i-n
  out.append((num,-12.7 if left else 12.7,round((n-1)*1.27-k*2.54,4),0 if left else 180))
 return out,max(3,(n-1)*1.27+2.54)

def libsym(p):
 name=p['ref'].replace('#','F');gg,h=geom(p)
 s=f'(symbol "VS:{name}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes)'
 for k,v,y in [('Reference',p['ref'],h+3),('Value',p['value'],h+1)]:s+=f'(property {q(k)} {q(v)} (at 0 {y} 0) {effect()})'
 s+=f'(symbol "{name}_0_1" (rectangle (start -10.16 {h}) (end 10.16 {-h}) (stroke (width 0.254) (type default)) (fill (type background))))'
 if len(gg)==2:s=s.replace('(start -10.16 2.54) (end 10.16 -2.54)', '(start -2.54 1.27) (end 2.54 -1.27)')
 s+=f'(symbol "{name}_1_1"'
 for num,x,y,angle in gg:
  typ=p['types'].get(num,'passive');nm=p['names'].get(num,num)
  s+=f'(pin {typ} line (at {x} {y} {angle}) (length 2.54) (name {q(nm)} {effect(0.9)}) (number {q(num)} {effect(0.9)}))'
 return s+'))'

def sheet(board,group,parts,index,rootid,sheetid):
 name=f'{board}_{index:02d}'
 path=ROOT/'hardware/kicad'/board/(name+'.kicad_sch')
 s=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {sheetid}) (paper "A3") (title_block (title {q("VideoSynth R1 / "+board+" / "+group)}) (date "2026-10-23") (rev "R1 PROTOTYPE") (company "Guadonna / VideoSynth") (comment 1 "NOT RELEASED FOR MANUFACTURE - see docs/r1/hardware.md"))'
 s+='(lib_symbols '+''.join(libsym(p) for p in parts)+')'
 for k,p in enumerate(parts):
  x=38.1+(k%6)*66.04;y=38.1+(k//6)*60.96
  gg,h=geom(p);sid=uid(board+'/'+p['ref']);lib='VS:'+p['ref'].replace('#','F')
  s+=f'(symbol (lib_id {q(lib)}) (at {x} {y} 0) (unit 1) (in_bom {"yes" if p["footprint"] else "no"}) (on_board {"yes" if p["footprint"] else "no"}) (dnp no) (uuid {sid})'
  for key,val,py,hidden in [('Reference',p['ref'],y-h-5,False),('Value',p['value'],y-h-2.5,False),('Footprint',p['footprint'],y,True),('Datasheet','',y,True)]:
   s+=f'(property {q(key)} {q(val)} (at {x} {py} 0) {effect(1,hidden)})'
  for num,_,_,_ in gg:s+=f'(pin {q(num)} (uuid {uid(sid+"/pin/"+num)}))'
  s+=f'(instances (project "videosynth_{board}" (path "/{rootid}/{sheetid}" (reference {q(p["ref"])}) (unit 1)))))'
  for num,px,py,ang in gg:
   ax=round(x+px,4);ay=round(y-py,4);net=p['pins'][num]
   if net is None:s+=f'(no_connect (at {ax} {ay}) (uuid {uid(sid+"/nc/"+num)}))';continue
   bx=round(ax+(-2.54 if px<0 else 2.54),4)
   s+=f'(wire (pts (xy {ax} {ay}) (xy {bx} {ay})) (stroke (width 0) (type default)) (uuid {uid(sid+"/w/"+num)}))'
   angle=180 if px<0 else 0
   s+=f'(global_label {q(net)} (shape bidirectional) (at {bx} {ay} {angle}) {effect(0.85)[:-1]+(" (justify right))" if px<0 else " (justify left))")} (uuid {uid(sid+"/lbl/"+num)}))'
 s+=f'(sheet_instances (path "/{rootid}/{sheetid}" (page "{index+1}"))))'
 path.write_text(s+'\n')
 return path

def schematics(board,parts):
 out=ROOT/'hardware/kicad'/board;out.mkdir(parents=True,exist_ok=True)
 (out/'VS.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator \"kicad_symbol_editor\") '+''.join(libsym(p).replace('\"VS:', '\"') for p in parts)+')\n')
 (out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name \"VS\") (type \"KiCad\") (uri \"${KIPRJMOD}/VS.kicad_sym\") (options \"\") (descr \"VideoSynth R1 pin-defined symbols\")))\n')
 rootid=uid(board+'/root');s=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {rootid}) (paper "A4") (title_block (title "VideoSynth R1 - {board}") (rev "R1 PROTOTYPE")) (lib_symbols)'
 groups=list(dict.fromkeys(p['group'] for p in parts));index=0
 for group in groups:
  pp=[p for p in parts if p['group']==group]
  for start in range(0,len(pp),24):
   index+=1;sheetid=uid(board+f'/sheet/{index}');file=sheet(board,group,pp[start:start+24],index,rootid,sheetid)
   x=25+((index-1)%2)*130;y=22+((index-1)//2)*40
   s+=f'(sheet (at {x} {y}) (size 105 25) (stroke (width 0.1524) (type default)) (fill (color 0 0 0 0.0)) (uuid {sheetid})'
   s+=f'(property "Sheetname" {q(group+" "+str(start//24+1))} (at {x} {y-1} 0) {effect()})'
   s+=f'(property "Sheetfile" {q(file.name)} (at {x} {y+26} 0) {effect()})'
   s+=f'(instances (project "videosynth_{board}" (path "/{rootid}" (page "{index+1}")))))'
 s+='(text "ELECTRICAL PROTOTYPE R1. PCB and simulation are not physical validation.\\nPower: Eurorack +12 V only. -12 V unused. Module USB FET2 must be removed.\\nSee hardware/design.json for exact pin mapping and docs/r1/ for assumptions." (at 25 185 0) (effects (font (size 1.4 1.4)) (justify left)) (uuid '+uid(board+'/note')+'))'
 s+='(sheet_instances (path "/" (page "1"))))'
 (out/f'videosynth_{board}.kicad_sch').write_text(s+'\n')
 # Explicit defaults, no disabled ERC/DRC checks.
 proj={'meta':{'filename':f'videosynth_{board}.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.20,'min_track_width':0.20,'min_via_diameter':0.6,'min_through_hole_diameter':0.3,'min_hole_to_hole':0.25,'min_copper_edge_clearance':0.3},'defaults':{'board_outline_line_width':0.05,'copper_line_width':0.2},'rule_severities':{}}},'net_settings':{'classes':[{'name':'Default','clearance':0.20,'track_width':0.20,'via_diameter':0.6,'via_drill':0.3,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.2,'diff_pair_gap':0.25,'diff_pair_via_gap':0.25,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)','wire_width':6,'bus_width':12,'line_style':0,'priority':0},{'name':'Power','clearance':0.20,'track_width':0.7,'via_diameter':0.6,'via_drill':0.3,'microvia_diameter':0.3,'microvia_drill':0.1,'diff_pair_width':0.2,'diff_pair_gap':0.25,'diff_pair_via_gap':0.25,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)','wire_width':6,'bus_width':12,'line_style':0,'priority':1}],'netclass_patterns':[{'pattern':n,'netclass':'Power'} for n in ['EUR_12','FUSED_12','VIN','SW','V5']]}}
 (out/f'videosynth_{board}.kicad_pro').write_text(json.dumps(proj,indent=2)+'\n')

def boardfile(board,parts):
 b=pcb.BOARD();cfg=BOARD_CONFIG[board];w,h=cfg['size'];b.SetCopperLayerCount(4)
 nets={}
 for n in sorted({v for p in parts for v in p['pins'].values() if v}):
  net=pcb.NETINFO_ITEM(b,n);b.Add(net);nets[n]=net
 issues=[]
 for p in parts:
  if not p['footprint']:continue
  lib,name=p['footprint'].split(':');fp=pcb.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',name)
  if not fp:issues.append('missing footprint '+p['footprint']);continue
  fp.SetReference(p['ref']);fp.SetValue(p['value']);fp.SetFPID(pcb.LIB_ID(lib,name));fp.SetPosition(point(*p['xy']));fp.SetOrientationDegrees(p['angle'])
  b.Add(fp)
  if p['side']=='B':fp.Flip(fp.GetPosition(),False)
  present={pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
  absent=set(p['pins'])-present
  if absent:issues.append(f'{board} {p["ref"]} missing pads {absent} in {name}')
  extra=present-set(p['pins'])
  if extra:issues.append(f'{board} {p["ref"]} extra pads {extra} in {name}')
  for pad in fp.Pads():
   n=p['pins'].get(pad.GetNumber());
   if n:pad.SetNet(nets[n])
  fp.Reference().SetLayer(pcb.B_Fab if p['side']=='B' else pcb.F_Fab);fp.Reference().SetTextSize(point(0.8,0.8));fp.Reference().SetTextThickness(pcb.FromMM(.12));fp.Value().SetVisible(False)
 for (x1,y1,x2,y2) in [(0,0,w,0),(w,0,w,h),(w,h,0,h),(0,h,0,0)]:
  e=pcb.PCB_SHAPE();e.SetShape(pcb.SHAPE_T_SEGMENT);e.SetStart(point(x1,y1));e.SetEnd(point(x2,y2));e.SetLayer(pcb.Edge_Cuts);e.SetWidth(pcb.FromMM(.05));b.Add(e)
 for i,(x,y) in enumerate(cfg['holes']):
  fp=pcb.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_3.2mm_M3');fp.SetReference(f'H{i+1}');fp.SetPosition(point(x,y));fp.Value().SetVisible(False);fp.Reference().SetLayer(pcb.F_Fab);b.Add(fp)
 # Dedicated label, size modest; no manufacturing marks or datecode claim.
 txt=pcb.PCB_TEXT(b);txt.SetText('VideoSynth R1 / '+board+' / PROTOTYPE');txt.SetPosition(point(w/2,3));txt.SetTextSize(point(1,1));txt.SetTextThickness(pcb.FromMM(.15));txt.SetLayer(pcb.F_SilkS);b.Add(txt)
 if board=='core':
  # Assembly envelope of OLIMEX module, based on upstream PCB coordinates.
  for x1,y1,x2,y2 in [(10.3,8.37,40.3,8.37),(40.3,8.37,40.3,80.37),(40.3,80.37,10.3,80.37),(10.3,80.37,10.3,8.37)]:
   e=pcb.PCB_SHAPE();e.SetShape(pcb.SHAPE_T_SEGMENT);e.SetStart(point(x1,y1));e.SetEnd(point(x2,y2));e.SetLayer(pcb.Dwgs_User);e.SetWidth(pcb.FromMM(.2));b.Add(e)
 z=pcb.ZONE(b);z.SetLayer(pcb.In1_Cu);z.SetNet(nets['GND']);z.SetLocalClearance(pcb.FromMM(.25));z.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(pcb.FromMM(.25));z.SetThermalReliefSpokeWidth(pcb.FromMM(.35));z.SetMinThickness(pcb.FromMM(.2));z.Outline().NewOutline()
 for zx,zy in [(.4,.4),(w-.4,.4),(w-.4,h-.4),(.4,h-.4)]:z.Outline().Append(round(zx*1e6),round(zy*1e6))
 b.Add(z)
 if issues:raise RuntimeError('\n'.join(issues))
 path=ROOT/'hardware/kicad'/board/f'videosynth_{board}.kicad_pcb';pcb.SaveBoard(str(path),b)
 print(board,len(b.GetFootprints()),'footprints',len(nets),'nets')
 # DSN is exported from a freshly loaded board in a separate process.
 # KiCad 9 SWIG export can crash on a newly generated in-memory board.

if __name__=='__main__':
 dump()
 for board in BOARD_CONFIG:
  ps=[p for p in PARTS if p['board']==board];schematics(board,ps)
  if '--schematics-only' not in sys.argv:boardfile(board,ps)
