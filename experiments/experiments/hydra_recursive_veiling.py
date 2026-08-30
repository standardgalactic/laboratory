"""HYDRA: signal recoverability through nested translucent veils."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("hydra_recursive_veiling"); begin(a)
signal=mat("Signal",AMBER,emission=2); visible=mat("Recovered trace",CYAN,emission=1.5)
veils=[mat(f"Veil {i}",(0.18+i*.08,.25,.55+i*.08,1),alpha=.12+i*.04,roughness=.15) for i in range(4)]
for i,m in enumerate(veils): sphere(f"Recursive veil {i}",1.35+i*.72,(0,0,3.2),m,3)
pts=[]
for i in range(100):
    t=i/99; r=.25+3.5*t; ang=t*math.tau*2.4; pts.append((r*math.cos(ang),r*math.sin(ang),1.1+4.1*t))
curve("Hidden signal",pts,signal,.045)
for i in range(8):
    p=pts[12+i*11]; sphere(f"Visibility sample {i}",.1,p,visible if i%3 else signal)
for i,r in enumerate((1.35,2.07,2.79,3.51)): torus(f"Visibility threshold {i}",r,.03,(0,0,3.2),visible)
floor(); text("RECURSIVE VEILING / VISIBILITY THRESHOLDS",(0,-5.8,.02),.29)
camera((12,-17,10),(0,0,3),56); lights(); finish(a)

