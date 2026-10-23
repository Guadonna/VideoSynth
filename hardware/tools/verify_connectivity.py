"""Compare schematic XML, design manifest and every PCB pad, including NCs."""
from pathlib import Path
import os,json,xml.etree.ElementTree as ET,hashlib
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
root=Path(__file__).resolve().parents[2];design=json.loads((root/'hardware/design.json').read_text());summary={}
for name in ['core','panel']:
 parts=[x for x in design['parts'] if x['board']==name and x['footprint']];expected={(x['ref'],num):net for x in parts for num,net in x['pins'].items()};sch={}
 xml=ET.parse(root/f'hardware/verification/{name}-netlist.xml')
 for net in xml.findall('./nets/net'):
  for node in net.findall('node'):sch[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
 boardpath=root/f'hardware/kicad/{name}/videosynth_{name}.kicad_pcb';b=p.LoadBoard(str(boardpath));pads={}
 for f in b.GetFootprints():
  for pa in f.Pads():
   if pa.GetNumber():pads[(f.GetReference(),pa.GetNumber())]=pa.GetNetname() or None
 assert pads.keys()==expected.keys(),(name,'pad sets differ',pads.keys()^expected.keys())
 for key,net in expected.items():
  assert pads[key]==net,(name,'PCB net mismatch',key,net,pads[key])
  if net is not None:assert sch.get(key)==net,(name,'schematic mismatch',key,net,sch.get(key))
  else:assert key not in sch or sch[key].startswith('unconnected-'),(name,'NC connected',key,sch.get(key))
 drc=json.loads((root/f'hardware/verification/{name}-drc.json').read_text())
 assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity'],(name,'DRC not clean')
 assert 'ERC messages: 0  Errors 0  Warnings 0' in (root/f'hardware/verification/{name}-erc.txt').read_text()
 summary[name]={'parts':len(parts),'unique_numbered_pads':len(pads),'nets':len(set(n for n in expected.values() if n)),'schematic_to_manifest':'PASS','pcb_to_manifest':'PASS','drc_violations':0,'unconnected_items':0,'erc_violations':0,'pcb_sha256':hashlib.sha256(boardpath.read_bytes()).hexdigest()}
# Cross-board harness is pin-for-pin, not mirrored.
byref={(x['board'],x['ref']):x for x in design['parts']}
assert byref['core','J5']['pins']==byref['panel','J1']['pins']
# Safety-critical power intentions, verified independently of all-pad comparison.
assert byref['core','J1']['pins']=={'1':None,'2':None,**{str(i):'GND' for i in range(3,9)},'9':'EUR_12','10':'EUR_12'}
assert byref['core','J4']['pins']['1'] is None
assert byref['core','J2']['pins']=={'1':'V5','2':'GND'}
summary['scope']='Connectivity/ERC/DRC only; not semiconductor pinout certification, physical validation, SI or power integrity.'
(root/'hardware/verification/connectivity-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
