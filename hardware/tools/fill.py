import os,sys
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
for path in sys.argv[1:]:
 b=p.LoadBoard(path);b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(path,b);print('filled',path)
