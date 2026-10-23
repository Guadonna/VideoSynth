import os,sys,json
os.environ.setdefault('XDG_CONFIG_HOME','/workspace/.config')
import pcbnew as p
boardfile,session=sys.argv[1:3]
b=p.LoadBoard(boardfile)
assert p.ImportSpecctraSES(b,session),'SES import failed'
p.SaveBoard(boardfile,b)
print(len(b.GetTracks()),'track/via items imported')
