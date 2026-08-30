"""spherepop: four input cases executed through primitive logic stages."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("spherepop_logic"); begin(a)
off=mat("False",(0.08,.12,.16,1)); on=mat("True",GREEN,emission=1.4); bind=mat("Bind",VIOLET,emission=1); refuse=mat("Refuse",RED,emission=1.5); pop=mat("Pop",CYAN,emission=1.5); neutral=mat("Neutral text",PAPER,emission=.3)
cases=((0,0,0),(0,1,0),(1,0,0),(1,1,1))
for row,(x,y,out) in enumerate(cases):
    yy=3-row*1.7
    sphere(f"A={x}",.28,(-5,yy,1),on if x else off); sphere(f"B={y}",.28,(-3.8,yy,1),on if y else off)
    segment("BIND",(-3.45,yy,1),(-1.2,yy,1),bind,.06)
    sphere("Bound pair",.34,(-.8,yy,1),bind if x and y else refuse)
    segment("POP or REFUSE",(-.4,yy,1),(2.0,yy,1),pop if out else refuse,.06)
    sphere(f"AND output {out}",.38,(2.5,yy,1),on if out else off)
    text(f"{x}{y} → {out}",(4.0,yy,.94),.3,on if out else neutral,align="LEFT")
floor(); text("BIND  →  REFUSE | POP  /  AND",(0,-4.4,.02),.32)
camera((12,-18,10),(0,0,1.2),58); lights(); finish(a)
