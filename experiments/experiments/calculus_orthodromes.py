"""calculus: orthodromic infrastructure and libration visibility."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("calculus_orthodromes"); begin(a)
earth=mat("Earth",(0.025,0.18,0.35,1),metallic=.15,roughness=.28)
rings=[mat("Polar",CYAN,emission=1.5),mat("Tilted",VIOLET,emission=1.3),mat("Libration",AMBER,emission=1.4)]
sphere("Reference sphere",3,(0,0,3.2),earth,3)
for i in range(4): torus(f"Polar orthodrome {i}",3.08,.035,(0,0,3.2),rings[0],(math.pi/2,0,i*math.pi/4))
for i in range(4): torus(f"Tilted orthodrome {i}",3.12,.045,(0,0,3.2),rings[1],(math.radians(55),0,i*math.pi/2))
orbit=[]
for i in range(120):
    t=i*math.tau/119; orbit.append((4.7*math.cos(t),4.7*math.sin(t),3.2+.55*math.sin(2*t)))
curve("Libration envelope",orbit,rings[2],.055,True)
for i in range(9):
    t=i*math.tau/9; sphere(f"Libration sample {i}",.13,(4.7*math.cos(t),4.7*math.sin(t),3.2+.55*math.sin(2*t)),rings[2])
floor(); text("ORTHODROMES / LIBRATION ENVELOPE",(0,-6.0,.02),.3)
camera((13,-17,11),(0,0,3.0),55); lights(); finish(a)

