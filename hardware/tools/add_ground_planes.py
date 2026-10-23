"""Add dedicated GND planes and short stitching connections to a routed board.
No unconnected-item or clearance errors are waived. Final KiCad DRC is required.
"""
import os,sys,math,json
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
from pathlib import Path
from design import BOARD_CONFIG

def xy(v):return (v.x/1e6,v.y/1e6)
def pt(v):return p.VECTOR2I(round(v[0]*1e6),round(v[1]*1e6))
def segdist(a,b,c):
 dx=b[0]-a[0];dy=b[1]-a[1];d=dx*dx+dy*dy
 t=max(0,min(1,((c[0]-a[0])*dx+(c[1]-a[1])*dy)/d)) if d else 0
 return math.hypot(c[0]-a[0]-t*dx,c[1]-a[1]-t*dy)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def segsep(a,b,c,d):
 if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:return 0
 return min(segdist(a,b,c),segdist(a,b,d),segdist(c,d,a),segdist(c,d,b))
def recthit(a,b,r,gap):
 x1,y1,x2,y2=r;x1-=gap;y1-=gap;x2+=gap;y2+=gap
 t0,t1=0.,1.;dx=b[0]-a[0];dy=b[1]-a[1]
 for dd,qq in [(-dx,a[0]-x1),(dx,x2-a[0]),(-dy,a[1]-y1),(dy,y2-a[1])]:
  if abs(dd)<1e-12:
   if qq<0:return False
  else:
   t=qq/dd
   if dd<0:t0=max(t0,t)
   else:t1=min(t1,t)
   if t0>t1:return False
 return True
name=sys.argv[1];path=Path('hardware/kicad')/name/f'videosynth_{name}.kicad_pcb'
b=p.LoadBoard(str(path));b.SetCopperLayerCount(4)
gnd=next(n for n in b.GetNetsByNetcode().values() if n.GetNetname()=='GND')
# Snapshot copper obstacles. THT pads exist on all layers; bounding boxes are conservative.
obs=[]; holes=[]
for f in b.GetFootprints():
 for pad in f.Pads():
  bb=pad.GetBoundingBox();r=(bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
  layers={p.F_Cu,p.B_Cu} if pad.GetAttribute()!=p.PAD_ATTRIB_SMD else {p.B_Cu if pad.IsOnLayer(p.B_Cu) else p.F_Cu}
  if pad.GetNetname()!='GND':obs.append((r,layers))
  if pad.GetDrillSize().x:holes.append((xy(pad.GetPosition()),max(pad.GetDrillSize().x,pad.GetDrillSize().y)/2e6))
tracks=[]
for t in b.GetTracks():
 if t.GetNetname()=='GND':continue
 tracks.append((xy(t.GetStart()),xy(t.GetEnd()),(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/2e6,{p.F_Cu,p.B_Cu} if isinstance(t,p.PCB_VIA) else {t.GetLayer()}))
size=BOARD_CONFIG[name]['size'];failed=[];added=0
for f in b.GetFootprints():
 for pad in f.Pads():
  if pad.GetNetname()!='GND' or pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
  a=xy(pad.GetPosition());layer=p.B_Cu if pad.IsOnLayer(p.B_Cu) else p.F_Cu;found=None
  for dist in [1.2,1.25,1.3,1.35,1.4,1.45,1.5,1.6,1.8,2.,2.6,3.2,4.,5.,6.]:
   for angle in range(0,360,15):
    rad=math.radians(angle);v=(a[0]+dist*math.cos(rad),a[1]+dist*math.sin(rad))
    if not(0.6<v[0]<size[0]-.6 and .6<v[1]<size[1]-.6):continue
    if any(math.dist(v,c)<r+.15+.25 for c,r in holes):continue
    if any(recthit(v,v,r,.501) or (layer in layers and recthit(a,v,r,.301)) for r,layers in obs):continue
    if any(segdist(c,d,v)<radius+.501 or (layer in layers and segsep(a,v,c,d)<radius+.301) for c,d,radius,layers in tracks):continue
    found=v;break
   if found:break
  corner=None
  if not found:
   for dx in [1.2,-1.2,1.6,-1.6,2.,-2.,2.6,-2.6,3.2,-3.2,4.,-4.]:
    turn=(a[0]+dx,a[1])
    if any(layer in layers and recthit(a,turn,r,.301) for r,layers in obs):continue
    if any(layer in layers and segsep(a,turn,c,d)<radius+.301 for c,d,radius,layers in tracks):continue
    for dy in [.8,-.8,1.2,-1.2,1.6,-1.6,2.4,-2.4,3.2,-3.2,4.,-4.,5.,-5.]:
     v=(turn[0],turn[1]+dy)
     if not(.6<v[0]<size[0]-.6 and .6<v[1]<size[1]-.6):continue
     if any(math.dist(v,c)<r+.4 for c,r in holes):continue
     if any(recthit(v,v,r,.501) or (layer in layers and recthit(turn,v,r,.301)) for r,layers in obs):continue
     if any(segdist(c,d,v)<radius+.501 or (layer in layers and segsep(turn,v,c,d)<radius+.301) for c,d,radius,layers in tracks):continue
     found=v;corner=turn;break
    if found:break
  if not found:failed.append(f.GetReference()+'.'+pad.GetNumber());continue
  via=p.PCB_VIA(b);via.SetPosition(pt(found));via.SetWidth(p.F_Cu,p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(gnd);b.Add(via)
  tr=p.PCB_TRACK(b);tr.SetStart(pad.GetPosition());tr.SetEnd(pt(corner or found));tr.SetWidth(p.FromMM(.2));tr.SetLayer(layer);tr.SetNet(gnd);b.Add(tr);holes.append((found,.15));added+=1
  if corner:
   tr2=p.PCB_TRACK(b);tr2.SetStart(pt(corner));tr2.SetEnd(pt(found));tr2.SetWidth(p.FromMM(.2));tr2.SetLayer(layer);tr2.SetNet(gnd);b.Add(tr2)
for layer in ([] if len(b.Zones()) else [p.In1_Cu]):
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(gnd);z.SetLocalClearance(p.FromMM(.25));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.35));z.SetMinThickness(p.FromMM(.2))
 z.Outline().NewOutline()
 for x,y in [(.4,.4),(size[0]-.4,.4),(size[0]-.4,size[1]-.4),(.4,size[1]-.4)]:z.Outline().Append(round(x*1e6),round(y*1e6))
 b.Add(z)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
print(name,'ground vias',added,'unresolved',failed)
