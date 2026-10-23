import os,sys,re
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
from pathlib import Path
b=p.LoadBoard(sys.argv[1]);print('Export',sys.argv[1],flush=True)
assert p.ExportSpecctraDSN(b,sys.argv[2])
f=Path(sys.argv[2]);s=f.read_text();via_name=re.search(r'\(via \"([^\"]+)\"',s).group(1)
# KiCad SWIG DSN does not load project netclass rules. Set them explicitly.
start=s.index('    (class kicad_default ');end=s.index('      (circuit',start)
head=s[start:end]
power=[n for n in ['EUR_12','FUSED_12','VIN','SW','V5'] if re.search(r'(?<!\w)'+n+r'(?!\w)',head)]
for n in power+['GND']:head=re.sub(r'(?<!\w)'+n+r'(?!\w)','',head)
s=s[:start]+head+s[end:]
s=s.replace('  (wiring','  (wiring')
pos=s.rfind('  )\n  (wiring')
classes='    (class Ground GND (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 300) (clearance 200)))\n'
if power:classes+='    (class Power '+' '.join(power)+' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 700) (clearance 200)))\n'
classes=classes.replace('Via[0-1]_600:300_um',via_name)
s=s[:pos]+classes+s[pos:];s=s.replace('(layer In1.Cu\n      (type signal)', '(layer In1.Cu\n      (type power)');f.write_text(s)
