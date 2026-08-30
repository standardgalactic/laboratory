"""Chloroplasts: proton accumulation and ATP-synthase transport."""
import math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("chloroplast_proton_gradient"); begin(a)
mem=mat("Membrane",GREEN,emission=.25); proton=mat("Protons",AMBER,emission=1.8); flow=mat("Synthase flow",CYAN,emission=1.6); rotor=mat("ATP synthase",VIOLET,emission=1)
for z in (1.6,3.8): cube(f"Thylakoid membrane {z}",(5,.18,.12),(0,0,z),mem)
for i in range(70):
    x=random.uniform(-4.7,4.7); y=random.uniform(-.6,.6); z=random.uniform(1.9,3.5)
    sphere(f"Proton {i}",.055,(x,y,z),proton,1)
for x in (-3,-1,1,3):
    cylinder("ATP synthase channel",.22,2.2,(x,0,2.7),rotor)
    torus("Synthase rotor",.42,.07,(x,0,1.35),rotor)
    pts=[(x+.34*math.cos(t),.34*math.sin(t),3.5-2.1*t/(math.tau*2)) for t in [i*math.tau*2/60 for i in range(61)]]
    curve("Proton descent",pts,flow,.035)
floor(); text("PROTON GRADIENT / ROTARY TRANSPORT",(0,-4.4,.02),.31)
camera((11,-16,9),(0,0,2.5),58); lights(); finish(a)

