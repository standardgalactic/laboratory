"""cliodynamics: consequential aliasing under selective projection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("cliodynamics_aliasing"); begin(a)
state=mat("World states",CYAN,emission=1); projection=mat("Projection",VIOLET,emission=1.4); divergent=mat("Divergent actions",AMBER,emission=1.3); warning=mat("Aliasing",RED,emission=2)
s1=(-4,2,2); s2=(-4,-2,2); alias=(0,0,2); a1=(4,2.5,2); a2=(4,-2.5,2)
for name,pos,m in (("State S1",s1,state),("State S2",s2,state),("Same projection",alias,warning),("Continue A",a1,divergent),("Continue B",a2,divergent)): sphere(name,.48,pos,m)
for x,y in ((s1,alias),(s2,alias)): segment("Selective projection",x,y,projection,.075)
for x,y in ((alias,a1),(alias,a2)): segment("Required continuation",x,y,divergent,.075)
text("S₁",(-4,2,1.25),.32); text("S₂",(-4,-2,1.25),.32); text("Π(S₁)=Π(S₂)",(0,0,1.2),.27,warning)
floor(); text("SAME VIEW / DIFFERENT REQUIRED ACTION",(0,-5.2,.02),.3)
camera((11,-16,10),(0,0,1.7),58); lights(); finish(a)

