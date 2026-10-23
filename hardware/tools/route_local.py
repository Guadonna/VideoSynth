"""Connect a selected DRC airwire with grid A*, preserving 0.2 mm clearance.
Usage: board.kicad_pcb drc.json airwire_index. Always rerun KiCad DRC afterwards.
This is a finishing aid, not an electrical or signal-integrity verification.
"""
import os,sys,json,math,heapq
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
path,report,index=sys.argv[1:4];b=p.LoadBoard(path);L=[p.F_Cu,p.In2_Cu,p.B_Cu];step=.1
items={i.m_Uuid.AsString():i for i in b.GetTracks()}
for f in b.GetFootprints():
 for pa in f.Pads():items[pa.m_Uuid.AsString()]=pa
pair=json.load(open(report))['unconnected_items'][int(index)]['items'];a,c=[items[i['uuid']] for i in pair];net=a.GetNet();name=a.GetNetname()
def xy(v):return v.x/1e6,v.y/1e6
def pt(v):return p.VECTOR2I(round(v[0]*1e6),round(v[1]*1e6))
start=(pair[0]['pos']['x'],pair[0]['pos']['y']);end=(pair[1]['pos']['x'],pair[1]['pos']['y']);margin=12
ox=math.floor((min(start[0],end[0])-margin)/step)*step;oy=math.floor((min(start[1],end[1])-margin)/step)*step
nx=math.ceil((abs(start[0]-end[0])+2*margin)/step)+3;ny=math.ceil((abs(start[1]-end[1])+2*margin)/step)+3;size=nx*ny
blocked=[bytearray(size) for _ in L];vb=bytearray(size)
def boxrange(x1,y1,x2,y2):return range(max(0,math.floor((x1-ox)/step)),min(nx,math.ceil((x2-ox)/step)+1)),range(max(0,math.floor((y1-oy)/step)),min(ny,math.ceil((y2-oy)/step)+1))
def rect(target,r,gap):
 x1,y1,x2,y2=r;xs,ys=boxrange(x1-gap,y1-gap,x2+gap,y2+gap)
 for iy in ys:
  if y1-gap<=oy+iy*step<=y2+gap:
   for ix in xs:
    if x1-gap<=ox+ix*step<=x2+gap:target[iy*nx+ix]=1

def capsule(target,a,c,r):
 xs,ys=boxrange(min(a[0],c[0])-r,min(a[1],c[1])-r,max(a[0],c[0])+r,max(a[1],c[1])+r);dx=c[0]-a[0];dy=c[1]-a[1];ll=dx*dx+dy*dy
 for iy in ys:
  y=oy+iy*step
  for ix in xs:
   x=ox+ix*step;t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/ll)) if ll else 0
   if (x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2<=r*r:target[iy*nx+ix]=1
for f in b.GetFootprints():
 for pa in f.Pads():
  bb=pa.GetBoundingBox();r=(bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6)
  rect(vb,r,.502 if pa.GetNetname()!=name else .35)
  if pa.GetNetname()!=name:
   for il,layer in enumerate(L):
    if pa.IsOnLayer(layer):rect(blocked[il],r,.302)
  if pa.GetDrillSize().x:
   pos=xy(pa.GetPosition());capsule(vb,pos,pos,max(pa.GetDrillSize().x,pa.GetDrillSize().y)/2e6+.401)
for t in b.GetTracks():
 via=isinstance(t,p.PCB_VIA);aa=xy(t.GetStart());cc=xy(t.GetEnd());rad=(t.GetWidth(p.F_Cu) if via else t.GetWidth())/2e6
 if t.GetNetname()!=name:
  capsule(vb,aa,cc,rad+.502)
  for il,layer in enumerate(L):
   if via or t.GetLayer()==layer:capsule(blocked[il],aa,cc,rad+.302)
 elif via:capsule(vb,aa,cc,.551)
# constrain to board's rectangular edge envelope
bb=b.GetBoardEdgesBoundingBox();xmin,ymin,xmax,ymax=bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6
for iy in range(ny):
 for ix in range(nx):
  if not(xmin+.61<ox+ix*step<xmax-.61 and ymin+.61<oy+iy*step<ymax-.61):
   k=iy*nx+ix;vb[k]=1
   for bl in blocked:bl[k]=1

def layers(item):return [i for i,l in enumerate(L) if item.IsOnLayer(l)]
def near(v):
 ix=round((v[0]-ox)/step);iy=round((v[1]-oy)/step);return iy*nx+ix
sk,ek=near(start),near(end);ends={il*size+ek for il in layers(c)};dist={};prev={};heap=[]
def h(k):
 il,kk=divmod(k,size);y,x=divmod(kk,nx);return math.hypot(ox+x*step-end[0],oy+y*step-end[1])/step
for il in layers(a):
 if not blocked[il][sk]:key=il*size+sk;dist[key]=0;heapq.heappush(heap,(h(key),0,key))
neighbors=[(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,1.414214),(-1,1,1.414214),(1,-1,1.414214),(1,1,1.414214)]
found=None
while heap:
 _,cost,key=heapq.heappop(heap)
 if cost>dist[key]+1e-7:continue
 if key in ends:found=key;break
 il,k=divmod(key,size);y,x=divmod(k,nx)
 candidates=[]
 for dx,dy,dd in neighbors:
  xx=x+dx;yy=y+dy
  if not(0<=xx<nx and 0<=yy<ny):continue
  kk=yy*nx+xx
  if blocked[il][kk] or (dx and dy and (blocked[il][y*nx+xx] or blocked[il][yy*nx+x])):continue
  candidates.append((il*size+kk,dd))
 if not vb[k]:
  for jl in range(3):
   if jl!=il and not blocked[jl][k]:candidates.append((jl*size+k,30))
 for key2,dd in candidates:
  nc=cost+dd
  if nc<dist.get(key2,1e30):dist[key2]=nc;prev[key2]=key;heapq.heappush(heap,(nc+h(key2),nc,key2))
if found is None:raise RuntimeError('No path '+name+' visited '+str(len(dist)))
keys=[found]
while keys[-1] in prev:keys.append(prev[keys[-1]])
keys.reverse();points=[]
for key in keys:
 il,k=divmod(key,size);y,x=divmod(k,nx);points.append((il,(ox+x*step,oy+y*step)))
points=[(points[0][0],start)]+points+[(points[-1][0],end)]
simple=[points[0]]
for i in range(1,len(points)-1):
 la,aa=simple[-1];lc,cc=points[i];ld,dd=points[i+1]
 if la!=lc or lc!=ld or abs((cc[0]-aa[0])*(dd[1]-cc[1])-(cc[1]-aa[1])*(dd[0]-cc[0]))>1e-8:simple.append(points[i])
simple.append(points[-1]);vias=set()
for (la,aa),(lc,cc) in zip(simple,simple[1:]):
 if la!=lc:
  if cc in vias:continue
  v=p.PCB_VIA(b);v.SetPosition(pt(cc));v.SetWidth(p.F_Cu,p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);b.Add(v);vias.add(cc)
 elif math.dist(aa,cc)>.001:
  t=p.PCB_TRACK(b);t.SetStart(pt(aa));t.SetEnd(pt(cc));t.SetLayer(L[la]);t.SetWidth(p.FromMM(.2));t.SetNet(net);b.Add(t)
p.SaveBoard(path,b);print('Connected',name,start,end,'vias',len(vias),'vertices',len(simple),'search',len(dist),flush=True);os._exit(0)
