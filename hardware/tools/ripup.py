import os,sys
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
path=sys.argv[1];b=p.LoadBoard(path);removed=[]
for t in list(b.GetTracks()):
 if t.GetNetname() in sys.argv[2:]:b.Remove(t);removed.append(t)
p.SaveBoard(path,b);print('Rip-up',sys.argv[2:],len(removed),'items',flush=True)
os._exit(0)
