"""calculus: weighted spherical service regions and secondary connections."""
import math, random, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("calculus_spherical_voronoi"); begin(a)
globe=mat("Globe",(0.025,.14,.26,1),metallic=.15,roughness=.3)
primary=mat("Primary hubs",AMBER,emission=1.5); edge=mat("Service edges",CYAN,emission=1.2); secondary=mat("Secondary network",VIOLET,emission=1)
sphere("Service globe",3,(0,0,3.2),globe,3)
hubs=[]
for i in range(11):
    z=1-2*(i+.5)/11; theta=i*math.pi*(3-math.sqrt(5)); r=math.sqrt(1-z*z)
    p=Vector((3.06*r*math.cos(theta),3.06*r*math.sin(theta),3.2+3.06*z)); hubs.append(p)
    sphere(f"Weighted hub {i}",.11+(i%3)*.035,p,primary)
for i,p in enumerate(hubs):
    nearest=sorted(((p-q).length,j) for j,q in enumerate(hubs) if j!=i)[:3]
    for _,j in nearest:
        if j<i: continue
        q=hubs[j]; pts=[]
        for k in range(20):
            t=k/19; v=((1-t)*(p-Vector((0,0,3.2)))+t*(q-Vector((0,0,3.2)))).normalized()*3.1+Vector((0,0,3.2)); pts.append(v)
        curve("Spherical Delaunay candidate",pts,secondary if (i+j)%3 else edge,.025)
floor(); text("WEIGHTED SERVICE REGIONS / SECONDARY NETWORK",(0,-6,.02),.27)
camera((13,-17,11),(0,0,3.1),55); lights(); finish(a)

