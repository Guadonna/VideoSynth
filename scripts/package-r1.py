"""Package reviewable source artifacts; exclude dependencies, caches and older ZIPs."""
from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parents[1];files=[]
for folder in ['app','firmware','hardware','scripts','tests','docs']:
 for f in (root/folder).rglob('*'):
  if not f.is_file() or '__pycache__' in f.parts or f.suffix in ['.zip','.pyc','.kicad_prl','.lck','.dsn']:continue
  files.append(f)
for n in ['README.md','.gitignore','package.json','package-lock.json','dist/VideoSynth-R1.html']:files.append(root/n)
manifest={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(files)}
out=root/'dist/VideoSynth-R1-prototype.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(files):z.write(f,'VideoSynth-R1/'+str(f.relative_to(root)))
 z.writestr('VideoSynth-R1/SHA256SUMS.json',json.dumps(manifest,indent=2)+'\n')
print(out.name,out.stat().st_size,'bytes',len(files),'files')
