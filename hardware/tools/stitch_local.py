"""Local grid search to escape a ground pad to an unobstructed through-via.
It preserves the 0.2 mm copper clearance and is followed by KiCad DRC.
"""
import os,sys,math,heapq
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
path=sys.argv[1];refs=sys.argv[2:];b=p.LoadBoard(path)
STEP=.1;N=241;HALF=N//2

def xy(v):return v.x/1e6,v.y/1e6
def pt(v):return p.VECTOR2I(round(v[0]*1e6),round(v[1]*1e6))
def route(spec):
 ref,num=spec.split('.');f=next(f for f in b.GetFootprints() if f.GetReference()==ref);pad=next(pa for pa in f.Pads() if pa.GetNumber()==num)
 sx,sy=xy(pad.GetPosition());net=pad.GetNet();name=pad.GetNetname();layer=p.B_Cu if pad.IsOnLayer(p.B_Cu) else p.F_Cu
 origin=(sx-HALF*STEP,sy-HALF*STEP);blocked=bytearray(N*N);via_blocked=bytearray(N*N)
 def coords(ix,iy):return origin[0]+ix*STEP,origin[1]+iy*STEP
 def boxrange(x1,y1,x2,y2):
  return range(max(0,math.floor((x1-origin[0])/STEP)),min(N,math.ceil((x2-origin[0])/STEP)+1)),range(max(0,math.floor((y1-origin[1])/STEP)),min(N,math.ceil((y2-origin[1])/STEP)+1))
 def rect(target,r,gap):
  x1,y1,x2,y2=r;xs,ys=boxrange(x1-gap,y1-gap,x2+gap,y2+gap)
  for iy in ys:
   y=origin[1]+iy*STEP
   if not y1-gap<=y<=y2+gap:continue
   for ix in xs:
    x=origin[0]+ix*STEP
    if x1-gap<=x<=x2+gap:target[iy*N+ix]=1
 def capsule(target,a,c,r):
  xs,ys=boxrange(min(a[0],c[0])-r,min(a[1],c[1])-r,max(a[0],c[0])+r,max(a[1],c[1])+r);dx=c[0]-a[0];dy=c[1]-a[1];length=dx*dx+dy*dy
  for iy in ys:
   y=origin[1]+iy*STEP
   for ix in xs:
    x=origin[0]+ix*STEP;t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/length)) if length else 0
    if (x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2<=r*r:target[iy*N+ix]=1
 for fp in b.GetFootprints():
  for pa in fp.Pads():
   bb=pa.GetBoundingBox();r=(bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
   if pa.GetNetname()!=name:
    rect(via_blocked,r,.501)
    if pa.IsOnLayer(layer):rect(blocked,r,.301)
   if pa.GetDrillSize().x:
    v=xy(pa.GetPosition());capsule(via_blocked,v,v,max(pa.GetDrillSize().x,pa.GetDrillSize().y)/2e6+.4)
 # Do not place an open via in the solder paste aperture of the source pad.
 bb=pad.GetBoundingBox();rect(via_blocked,(bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6),.35)
 for t in b.GetTracks():
  if t.GetNetname()==name:continue
  via=isinstance(t,p.PCB_VIA);a=xy(t.GetStart());c=xy(t.GetEnd());radius=(t.GetWidth(p.F_Cu) if via else t.GetWidth())/2e6
  capsule(via_blocked,a,c,radius+.501)
  if via or t.GetLayer()==layer:capsule(blocked,a,c,radius+.301)
 start=HALF*N+HALF
 if blocked[start]:print('BLOCKED SOURCE',spec);return False
 heap=[(0,start)];dist={start:0};parents={};target=None;neighbors=[(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,1.414),(-1,1,1.414),(1,-1,1.414),(1,1,1.414)]
 while heap:
  cost,k=heapq.heappop(heap)
  if cost>dist[k]+1e-6:continue
  iy,ix=divmod(k,N)
  if not via_blocked[k] and cost>=10:target=k;break
  for dx,dy,step in neighbors:
   nx=ix+dx;ny=iy+dy
   if not(0<=nx<N and 0<=ny<N):continue
   kk=ny*N+nx
   if blocked[kk] or (dx and dy and (blocked[iy*N+nx] or blocked[ny*N+ix])):continue
   nc=cost+step
   if nc<dist.get(kk,1e12):dist[kk]=nc;parents[kk]=k;heapq.heappush(heap,(nc,kk))
 if target is None:print('NO ESCAPE',spec,len(dist));return False
 points=[];k=target
 while k!=start:
  iy,ix=divmod(k,N);points.append(coords(ix,iy));k=parents[k]
 points.append((sx,sy));points.reverse()
 # Drop intermediate collinear vertices, retain exact pad origin.
 simple=[points[0]]
 for i in range(1,len(points)-1):
  a=simple[-1];c=points[i];d=points[i+1]
  if abs((c[0]-a[0])*(d[1]-c[1])-(c[1]-a[1])*(d[0]-c[0]))>1e-8:simple.append(c)
 simple.append(points[-1])
 v=p.PCB_VIA(b);v.SetPosition(pt(points[-1]));v.SetWidth(p.F_Cu,p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);b.Add(v)
 for a,c in zip(simple,simple[1:]):
  t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(c));t.SetWidth(p.FromMM(.2));t.SetLayer(layer);t.SetNet(net);b.Add(t)
 print('STITCH',spec,'via',points[-1],'length_mm',round(dist[target]*STEP,2),'vertices',len(simple),flush=True);return True
for ref in refs:route(ref)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(path,b)
