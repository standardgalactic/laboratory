"""autogenerative-dynamics: recursive growth and local repair after deletion."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *

a=args("autogenerative_repair"); begin(a)
old=mat("Inherited growth",CYAN,emission=.8); repair=mat("Repair growth",GREEN,emission=1.5); wound=mat("Deleted boundary",RED,emission=1.5)
def branch(origin,angle,length,depth,path=""):
    if depth==0:return
    end=(origin[0]+length*math.cos(angle),origin[1]+length*math.sin(angle),origin[2]+.65)
    is_gap=(end[0]>.2 and end[0]<2.4 and end[1]>-.8 and end[1]<1.4)
    if is_gap:
        sphere("Deletion boundary",.09,end,wound); return
    segment("Recursive branch "+path,origin,end,old,.045+depth*.008)
    branch(end,angle+.48,length*.72,depth-1,path+"L"); branch(end,angle-.48,length*.72,depth-1,path+"R")
for root in range(7): branch((-5+root*1.65,-3,.2),math.pi/2,1.5,5,str(root))
for i in range(7):
    t=i/6; curve("Repair bridge",((-0.2+t*.3,-.8,.8),(1.1,0,1.8),(2.5,1.4,2.7)),repair,.055)
floor(); text("RECURSIVE GROWTH / DELETION / REPAIR",(0,-5.3,.02),.3)
camera((12,-17,11),(0,0,2.1),55); lights(); finish(a)

