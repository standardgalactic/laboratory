"""Chloroplasts: thylakoid stacking, incidence angle, and absorbed paths."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("chloroplast_light_capture"); begin(a)
mem=mat("Thylakoid membrane",GREEN,emission=.35); light=mat("Incident light",AMBER,emission=2); absorbed=mat("Absorbed path",CYAN,emission=1.5); envelope=mat("Envelope",(0.15,.65,.4,1),alpha=.14)
sphere("Chloroplast envelope",4,(0,0,3.8),envelope,3)
for stack in range(-2,3):
    x=stack*1.25
    for layer in range(8): cylinder(f"Granum {stack} layer {layer}",.72,.10,(x,0,1.8+layer*.42),mem)
for ray in range(11):
    x=-4+ray*.8; start=(x,-5,8); hit=(x+2.2,0,3.5)
    segment("Incident photon",start,hit,light,.035)
    curve("Absorbed transfer",(hit,(x+1.2,0,2.7),(x+.5,0,2.1)),absorbed,.028)
floor(); text("INCIDENCE / STACKING / ABSORPTION",(0,-6,.02),.31)
camera((12,-17,11),(0,0,3.5),55); lights(); finish(a)

