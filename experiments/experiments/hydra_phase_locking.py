"""HYDRA: competing oscillatory personas and partial phase locking."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("hydra_phase_locking"); begin(a)
ms=[mat("Persona A",CYAN,emission=1.4),mat("Persona B",VIOLET,emission=1.4),mat("Persona C",AMBER,emission=1.4)]
centers=((-3,1,3),(3,1,3),(0,-3,3))
for j,(center,m) in enumerate(zip(centers,ms)):
    sphere(f"Persona attractor {j}",.55,center,m)
    for strand in range(7):
        pts=[]
        for i in range(65):
            t=i/64; r=4*(1-t)+.35; ang=strand*.8+t*math.tau*2.5+j*2.1
            pts.append((center[0]+r*math.cos(ang),center[1]+r*math.sin(ang),.5+2.5*t))
        curve(f"Persona {j} trajectory {strand}",pts,m,.025)
for i in range(3): segment("Cross-persona coupling",centers[i],centers[(i+1)%3],mat(f"Coupling {i}",GREEN,emission=.8),.035)
floor(); text("HYDRA / PARTIAL PHASE LOCKING",(0,-7,.02),.32)
camera((13,-18,12),(0,0,2.2),56); lights(); finish(a)

