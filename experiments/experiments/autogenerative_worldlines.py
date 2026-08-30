"""autogenerative-dynamics: candidate worldlines selected under constraints."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("autogenerative_worldlines"); begin(a)
candidate=mat("Candidate worldlines",VIOLET,emission=.8); accepted=mat("Admissible worldline",GREEN,emission=1.8); rejected=mat("Rejected",RED,emission=1.4); obstacle=mat("Constraint",AMBER,emission=.7,alpha=.32)
constraints=((-2,0,2.2),(0,1.2,3.0),(2,-.7,3.8))
for i,p in enumerate(constraints): sphere(f"Constraint region {i}",.85,p,obstacle,3)
for lane in range(11):
    pts=[]; valid=True
    for i in range(70):
        t=i/69; x=-5+10*t; y=(lane-5)*.35+math.sin(t*math.tau+lane)*.8; z=.6+4.5*t
        p=(x,y,z); pts.append(p)
        if any((Vector(p)-Vector(c)).length<.85 for c in constraints): valid=False
    m=accepted if valid and lane==8 else candidate if valid else rejected
    curve(f"{'Admissible' if valid else 'Rejected'} worldline {lane}",pts,m,.035 if m!=accepted else .075)
floor(); text("WORLDLINE SELECTION UNDER CONSTRAINT",(0,-5,.02),.31)
camera((13,-18,11),(0,0,2.5),55); lights(); finish(a)

