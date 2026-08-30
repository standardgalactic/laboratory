"""cliodynamics: system retention versus participant-indexed recoverability."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("cliodynamics_recoverability"); begin(a)
stored=mat("System retention",CYAN,emission=.8); seen=mat("Recoverable",GREEN,emission=1.4); hidden=mat("Retained but inaccessible",RED,emission=1.5); person=mat("Participants",VIOLET,emission=1)
for i in range(12):
    x=-5+i*.9; sphere(f"Retained event {i}",.16,(x,2.4,2.4),stored)
participants=((-3,-2,1.2),(0,-2,1.2),(3,-2,1.2))
for j,p in enumerate(participants):
    sphere(f"Participant {j}",.42,p,person)
    accessible={i for i in range(12) if (i+j*2)%3!=0 and abs(i-(3+j*3))<5}
    for i in range(12):
        x=-5+i*.9; m=seen if i in accessible else hidden
        if i in accessible: segment(f"Recoverability {j} {i}",p,(x,2.4,2.4),m,.018)
    text(f"R{j}",(p[0],-2.7,.7),.3,person)
floor(); text("RETENTION ≠ INDEXED RECOVERABILITY",(0,-4.5,.02),.32)
camera((12,-17,10),(0,0,1.8),58); lights(); finish(a)

