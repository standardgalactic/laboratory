"""TARTAN: trajectory-aware tiling under an annotated crack perturbation."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("tartan_annotated_fracture"); begin(a)
tile=mat("Stable tiles",CYAN,emission=.35); crack=mat("Annotated noise",RED,emission=2); brace=mat("Closure braces",GREEN,emission=1.3)
def fault_y(x): return .8*math.sin(x*.85)+.25*math.sin(x*2.1)
for ix in range(-7,8):
    for iy in range(-5,6):
        x,y=ix*.75,iy*.75; distance=abs(y-fault_y(x)); z=.65*math.exp(-distance*2)
        cube(f"Trajectory tile {ix} {iy}",(.34,.34,.08),(x,y,.12+z),crack if distance<.38 else tile)
pts=[(x/10,fault_y(x/10),1.05) for x in range(-55,56)]
curve("Annotated fracture trajectory",pts,crack,.065)
for i in range(-5,6,2):
    x=i; y=fault_y(x); segment("Reconciliation brace",(x,y-1,.45),(x,y+1,.45),brace,.055)
floor(); text("TRAJECTORY-AWARE TILING / ANNOTATED FRACTURE",(0,-5,.02),.28)
camera((12,-16,11),(0,0,.7),55); lights(); finish(a)

