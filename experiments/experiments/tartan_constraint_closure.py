"""TARTAN: local plausibility, obstruction, and staged closure."""
import math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("tartan_constraint_closure"); begin(a)
ok=mat("Consistent",CYAN,emission=.5); bad=mat("Obstruction",RED,emission=2); repaired=mat("Repaired",GREEN,emission=1.2)
for ix in range(-5,6):
  for iy in range(-5,6):
    conflict=(ix in (-1,0,1) and iy in (-1,0,1))
    z=.18*math.sin(ix*.7)*math.cos(iy*.6)+(1.0 if conflict else 0)
    m=bad if conflict and ix<0 else repaired if conflict else ok
    cube(f"Local section {ix} {iy}",(.43,.43,.10+abs(z)*.08),(ix*.92,iy*.92,.2+z),m)
for angle in range(0,360,30):
    t=math.radians(angle); curve("Closure force",((5*math.cos(t),5*math.sin(t),.4),(2*math.cos(t),2*math.sin(t),1.2),(0,0,1.1)),repaired,.025)
torus("Closure boundary",2.2,.055,(0,0,.35),repaired)
floor(); text("LOCAL FIT  →  OBSTRUCTION  →  CLOSURE",(0,-6,.02),.3)
camera((12,-16,12),(0,0,.8),55); lights(); finish(a)

