"""alphabet: ordinary language as a base with domain-specific fibers."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("alphabet_fibered_dsl"); begin(a)
base=mat("Base language",PAPER,emission=.25); domains=[mat("Logic",CYAN,emission=1),mat("Affect",VIOLET,emission=1),mat("Action",GREEN,emission=1)]; obstruction=mat("Translation obstruction",RED,emission=2)
for i in range(7):
    x=-4.5+i*1.5
    sphere(f"Base distinction {i}",.23,(x,0,.6),base)
    for level,m in enumerate(domains):
        z=1.5+level*1.25; sphere(f"Fiber {i} domain {level}",.18,(x,0,z),m); segment("Fiber lift",(x,0,.82 if level==0 else z-1.05),(x,0,z-.2),m,.025)
        if i<6: segment("Local transport",(x+.2,0,z),(x+1.3,0,z),m,.022)
segment("Failed cross-domain transport",(-1.5,0,4.0),(0,0,2.75),obstruction,.06); sphere("Obstruction",.3,(-.75,0,3.38),obstruction)
floor(); text("BASE LANGUAGE / DSL FIBERS / TRANSPORT",(0,-4.2,.02),.31)
camera((11,-16,9),(0,0,2.2),58); lights(); finish(a)

