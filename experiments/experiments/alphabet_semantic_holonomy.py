"""alphabet: semantic transport around a loop returns with residual drift."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("alphabet_semantic_holonomy"); begin(a)
domains=[mat("Domain A",CYAN,emission=1),mat("Domain B",VIOLET,emission=1),mat("Domain C",GREEN,emission=1),mat("Residual",RED,emission=2)]
centers=[]
for i in range(6):
    t=i*math.tau/6; p=(3.6*math.cos(t),3.6*math.sin(t),2.3+.45*math.sin(2*t)); centers.append(p)
    sphere(f"DSL chart {i}",.34,p,domains[i%3]); text(f"D{i}",(p[0],p[1]-.4,p[2]-.35),.22,domains[i%3])
for i,p in enumerate(centers):
    q=centers[(i+1)%6]; curve(f"Translation {i}",(p,((p[0]+q[0])*.52,(p[1]+q[1])*.52,3.5),q),domains[i%3],.055)
start=(centers[0][0],centers[0][1],centers[0][2]+.65); end=(start[0],start[1]+.75,start[2]+.35)
sphere("Initial meaning",.18,start,domains[0]); sphere("Returned meaning",.23,end,domains[3]); segment("Holonomy residue",start,end,domains[3],.055)
floor(); text("SEMANTIC TRANSPORT / HOLONOMY RESIDUE",(0,-5.2,.02),.29)
camera((12,-17,10),(0,0,2.5),56); lights(); finish(a)

