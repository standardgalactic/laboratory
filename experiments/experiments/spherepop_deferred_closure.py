"""spherepop: recursive containment with closure deferred across scopes."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("spherepop_deferred_closure"); begin(a)
scope=[mat("Scope outer",CYAN,emission=.9),mat("Scope middle",VIOLET,emission=1),mat("Scope inner",AMBER,emission=1.2)]
token=mat("Pending token",RED,emission=2); closed=mat("Committed closure",GREEN,emission=1.7)
for i,r in enumerate((4.2,2.9,1.6)): torus(f"Containment scope {i}",r,.07,(0,0,1.2+i*.7),scope[i])
path=[]
for i in range(100):
    t=i/99; r=4.4*(1-t)+.2; angle=t*math.tau*2.3; path.append((r*math.cos(angle),r*math.sin(angle),1+2*t))
curve("Deferred token history",path,token,.055)
for i in (20,48,76): sphere("Deferred boundary crossing",.16,path[i],token)
sphere("Closure",.48,path[-1],closed); text("COLLAPSE",(0,-.7,3.1),.25,closed)
floor(); text("RECURSIVE CONTAINMENT / DEFERRED CLOSURE",(0,-5.5,.02),.28)
camera((12,-17,11),(0,0,2),56); lights(); finish(a)

