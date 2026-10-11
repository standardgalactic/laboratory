import numpy as np, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"serif","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"pdf.fonttype":42})
OUT="/home/claude/resonance-without-regulation/"
t=16.04; nv=87.0
nu=np.linspace(60,120,600)
lo=(nu+nv)/2-np.sqrt(((nu-nv)/2)**2+t**2)
up=(nu+nv)/2+np.sqrt(((nu-nv)/2)**2+t**2)
fig,ax=plt.subplots(figsize=(5.6,3.7))
ax.plot(nu,lo,color="#1b4f72",lw=1.8,label="lower branch (MP$-$)")
ax.plot(nu,up,color="#922b21",lw=1.8,label="upper branch (MP$+$)")
ax.plot(nu,nu,color="0.55",lw=0.8,ls="--",label="uncoupled photon mode")
ax.axhline(nv,color="0.55",lw=0.8,ls=":",label="uncoupled CH$_2$ vibration")
ax.axhline(71.0,color="#1e8449",lw=1.0,label="reported feature, 71.0 THz")
def lower(x): return (x+nv)/2-math.sqrt(((x-nv)/2)**2+t**2)
for (lab,c0,a,b,col,dy) in (("m=2, $L$=2.2 $\\mu$m",90.85,76.9,111.0,"#b9770e",1),("m=1, $L$=1.2 $\\mu$m",83.28,71.4,99.9,"#6c3483",-1)):
    ax.axvspan(a,b,ymin=0,ymax=0.04,color=col,alpha=0.9,lw=0)
    ax.plot([c0],[lower(c0)],"o",color=col,ms=5)
    ax.annotate(f"{lab}\nlower {lower(c0):.1f} THz",(c0,lower(c0)),textcoords="offset points",xytext=(8,-26 if dy>0 else -34),fontsize=7.5,color=col)
ax.set_xlim(60,120); ax.set_ylim(55,125)
ax.set_xlabel("uncoupled cavity-photon frequency $\\nu_k$ (THz)")
ax.set_ylabel("hybrid mode frequency (THz)")
ax.legend(fontsize=7,frameon=False,loc="upper left")
fig.tight_layout(); fig.savefig(OUT+"fig_branches.pdf"); plt.close(fig)

k=np.linspace(0.2,1.3,300)
fig,ax=plt.subplots(figsize=(5.6,3.3))
ax.plot(k,nv-t*np.sqrt(k),color="#1b4f72",lw=1.8,label="lower branch")
ax.plot(k,nv+t*np.sqrt(k),color="#922b21",lw=1.8,label="upper branch")
ax.axhline(nv,color="0.55",lw=0.8,ls=":")
ax.plot([1.0],[71.0],"o",color="#1b4f72"); ax.plot([1.0],[103.04],"o",color="#922b21")
kk=(13/t)**2
ax.plot([kk],[74.0],"s",color="#1b4f72"); ax.plot([kk],[100.0],"s",color="#922b21")
ax.text(kk-0.02,62.5,f"$\\kappa$={kk:.2f}: 74.0 and 100.0 THz",fontsize=7.5,ha="right")
ax.text(1.02,62.5,"reference: 71.0 and 103.0 THz",fontsize=7.5,ha="left")
ax.axvspan(0.2,1.3,ymin=(90-55)/(125-55),ymax=(110-55)/(125-55),color="0.85",alpha=0.6,lw=0)
ax.text(0.22,112.5,"shaded: 90 to 110 THz, amide A and water (authors' stated obscuring range)",fontsize=7,color="0.3")
ax.set_ylim(55,125); ax.set_xlim(0.2,1.3)
ax.set_xlabel("relative oscillator density $\\kappa=\\rho/\\rho_0$ (at fixed $\\eta$, $\\mu$, resonance)")
ax.set_ylabel("branch frequency (THz)")
ax.legend(fontsize=7,frameon=False,loc="upper left")
fig.tight_layout(); fig.savefig(OUT+"fig_shift.pdf"); plt.close(fig)
print("ok")

# extra numbers
h=6.62607015e-34;c=2.99792458e8;kB=1.380649e-23
nu0=71e12
nbar=1/(math.exp(h*nu0/(kB*310))-1)
B=2*h*nu0**3/c**2*nbar
print("nbar",nbar,"B_nu W m-2 Hz-1 sr-1",B)
print("in-band 1 THz hemisphere W/m2:",B*1e12*math.pi,"-> uW/mm2:",B*1e12*math.pi*1e-6*1e6/1e6*1e0)
phot=10e-6/(h*nu0)
print("photons/s per 10uW:",phot," per mm2 at 12.7uW/mm2 ~",12.7e-6/(h*nu0))
# Fresnel
for n1,n2 in ((1.5,1.36),(1.5,1.38),(1.5,1.4)):
    R=((n1-n2)/(n1+n2))**2; F=math.pi*math.sqrt(R)/(1-R); print(n1,n2,"R",R,"finesse",F)
# deuteration
mu_h=12*1/13; mu_d=12*2/14
r=math.sqrt(mu_d/mu_h); print("reduced mass ratio sqrt",r," CD2 est THz",87/r)
for tr in (0.5,0.75,1.0):
    tp=16.04*tr; print("t' factor",tr,"lower",87/r-tp,"upper",87/r+tp)
# eta
print("eta_eff in-plane isotropic = 1/sqrt2",1/math.sqrt(2)," t ->",16.04/math.sqrt(2),"lower",87-16.04/math.sqrt(2),"upper",87+16.04/math.sqrt(2))
# t over nu
print("t/nu0",16.04/87)
# kT
print("kT kJ/mol at 310K",kB*310*6.02214076e23/1e3)
