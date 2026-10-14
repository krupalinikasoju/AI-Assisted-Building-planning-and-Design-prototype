
import io, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BuildWise AI", page_icon="🏗️", layout="wide")
st.markdown("""<div style="padding:22px;border-radius:16px;background:linear-gradient(110deg,#123047,#1b6b70);color:white"><h1>🏗️ BuildWise AI</h1><p>Architectural planning • Structural layout • Analysis • Element design • Estimation</p></div>""", unsafe_allow_html=True)
st.warning("Academic prototype only. This does not generate construction-ready plans or certified RCC designs. All outputs require review by qualified professionals using verified local rules, geotechnical data, applicable Indian Standards and project-specific loads.")

with st.sidebar:
    st.header("Project inputs")
    kind = st.selectbox("Building type", ["Residential", "Commercial", "Institutional"])
    location = st.text_input("Location", "Hyderabad, Telangana, India")
    area = st.number_input("Plot area (m²)", min_value=40.0, max_value=5000.0, value=150.0, step=10.0)

# Transparent placeholder assumptions, not a claim about local rules
coverage, far = 0.65, 1.5
footprint = area * coverage
max_floors = max(1, min(5, int((area * far) // max(footprint, 1))))
floor_options = list(range(1, max_floors + 1))
floor_names = {n: ("Ground floor" if n == 1 else f"G+{n-1} ({n} floors)") for n in floor_options}
selected = st.selectbox("Select a suggested floor option", floor_options,
    format_func=lambda n: f"{floor_names[n]} — approximate floor area {footprint*n:.1f} m²")

def room_layout(kind, w, d):
    if kind == "Residential":
        labels = [
            (0,.52,.52,.48,"Living / Dining"),(.52,.52,.48,.48,"Bedroom 1"),
            (0,.25,.34,.27,"Kitchen"),(.34,.25,.32,.27,"Lobby"),(.66,.25,.34,.27,"Bedroom 2"),
            (0,0,.23,.25,"Bath"),(.23,0,.23,.25,"Bath"),(.46,0,.30,.25,"Staircase"),(.76,0,.24,.25,"Utility")]
    elif kind == "Commercial":
        labels = [(0,.52,.66,.48,"Open Office / Shop"),(.66,.52,.34,.48,"Meeting"),
        (0,.25,.35,.27,"Reception"),(.35,.25,.35,.27,"Work Area"),(.70,.25,.30,.27,"Staircase"),
        (0,0,.30,.25,"Store"),(.30,0,.25,.25,"Washroom"),(.55,0,.22,.25,"Washroom"),(.77,0,.23,.25,"Services")]
    else:
        labels = [(0,.52,.65,.48,"Class / Activity"),(.65,.52,.35,.48,"Staff Room"),
        (0,.25,.35,.27,"Learning Space"),(.35,.25,.35,.27,"Lobby"),(.70,.25,.30,.27,"Staircase"),
        (0,0,.30,.25,"Store"),(.30,0,.25,.25,"Washroom"),(.55,0,.22,.25,"Washroom"),(.77,0,.23,.25,"Services")]
    return [(x*w,y*d,a*w,b*d,t) for x,y,a,b,t in labels]

w = math.sqrt(max(footprint,25)*1.25)
d = max(footprint,25)/w
rooms = room_layout(kind,w,d)

def save_png(fig):
    b=io.BytesIO(); fig.savefig(b,format="png",dpi=170,bbox_inches="tight"); b.seek(0); return b.getvalue()

st.header("1. Architectural planning")
st.write(f"**Location:** {location} · **Type:** {kind} · **Plot area:** {area:.1f} m²")
st.info(f"Illustrative assumptions: site coverage {coverage:.0%}, FAR {far:.2f}. These are placeholders, not verified local rules. Approximate footprint: {footprint:.1f} m².")
fig,ax=plt.subplots(figsize=(10,7))
ax.add_patch(Rectangle((0,0),w,d,fill=False,lw=3,color="#183a4a"))
for x,y,rw,rh,label in rooms:
    ax.add_patch(Rectangle((x,y),rw,rh,fill=False,lw=1.6,color="#526b75"))
    ax.text(x+rw/2,y+rh/2,label,ha="center",va="center",fontsize=8)
# schematic openings; these are illustrative marks, not construction details
for x in [w*.16,w*.42,w*.61,w*.84]: ax.plot([x,x+w*.06],[0,0],lw=5,color="#2d8c9b")
for y in [d*.36,d*.69]:
    ax.plot([0,0],[y,y+d*.10],lw=5,color="#d49b43")
    ax.plot([w,w],[y,y+d*.10],lw=5,color="#d49b43")
ax.annotate("",xy=(0,-d*.09),xytext=(w,-d*.09),arrowprops=dict(arrowstyle="<->"))
ax.text(w/2,-d*.15,f"Approx. width {w:.2f} m",ha="center",fontsize=9)
ax.annotate("",xy=(w*1.07,0),xytext=(w*1.07,d),arrowprops=dict(arrowstyle="<->"))
ax.text(w*1.13,d/2,f"{d:.2f} m",rotation=90,va="center",fontsize=9)
ax.text(w*.02,d*1.04,f"{floor_names[selected]} — conceptual 2D plan",weight="bold",fontsize=11)
ax.text(w*.02,d*1.005,"Blue: schematic door openings • Gold: schematic windows",fontsize=8)
ax.set_aspect("equal"); ax.set_xlim(-w*.05,w*1.22); ax.set_ylim(-d*.22,d*1.12); ax.axis("off"); fig.tight_layout()
st.pyplot(fig,use_container_width=True)
st.download_button("Download architectural plan (PNG)",save_png(fig),"architectural_plan.png","image/png")
st.caption("This is a room-layout concept, not a verified architectural drawing. Actual plot shape, north/road direction, setbacks, wall thicknesses, accessibility, plumbing, fire rules and openings need refinement.")

st.header("2. Coordinated structural layout")
nx=max(3,min(5,round(w/3.5)+1)); ny=max(3,min(4,round(d/3.5)+1))
xs=[i*w/(nx-1) for i in range(nx)]; ys=[i*d/(ny-1) for i in range(ny)]
figs,axs=plt.subplots(figsize=(9,6))
for x in xs: axs.plot([x,x],[0,d],color="#557b91",lw=1.5)
for y in ys: axs.plot([0,w],[y,y],color="#557b91",lw=1.5)
cols=[]; beams=[]; slabs=[]; foundations=[]
for j,y in enumerate(ys):
    for i,x in enumerate(xs):
        cid=f"C{j*len(xs)+i+1}"
        axs.scatter([x],[y],s=85,color="#173e5a",zorder=3); axs.text(x+w*.012,y+d*.012,cid,fontsize=8)
        cols.append({"ID":cid,"Type":"Column","Location":f"Grid {i+1}-{j+1}","Placeholder size":"300 × 300 mm"})
        foundations.append({"ID":f"F{len(foundations)+1}","Type":"Foundation","Location":f"Below {cid}","Placeholder size":"1.5 × 1.5 × 0.45 m"})
bid=1
for j,y in enumerate(ys):
    for i in range(len(xs)-1):
        axs.text((xs[i]+xs[i+1])/2,y+d*.018,f"B{bid}",fontsize=7,color="#9a5c18",ha="center")
        beams.append({"ID":f"B{bid}","Type":"Beam","Location":f"Grid {j+1}, bay {i+1}","Placeholder size":"230 × 450 mm"}); bid+=1
sid=1
for j in range(len(ys)-1):
    for i in range(len(xs)-1):
        axs.text((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2,f"S{sid}",fontsize=8,color="#287f71",ha="center")
        slabs.append({"ID":f"S{sid}","Type":"Slab","Location":f"Panel {i+1}-{j+1}","Placeholder size":"125 mm thick"}); sid+=1
axs.set_title("Conceptual grid: C = column, B = beam, S = slab panel")
axs.set_aspect("equal"); axs.set_xlim(-w*.04,w*1.04); axs.set_ylim(-d*.06,d*1.06); axs.axis("off"); figs.tight_layout()
st.pyplot(figs,use_container_width=True)
st.download_button("Download structural layout (PNG)",save_png(figs),"structural_layout.png","image/png")
st.caption("Structural positions and dimensions are illustrative placeholders, not designed member sizes. They must be coordinated with the actual architecture and engineered load path.")

st.header("3. Structural analysis — educational beam example")
st.write("This is a standalone simply supported beam example, not a full building analysis.")
c1,c2,c3=st.columns(3)
span=c1.number_input("Beam span (m)",2.0,10.0,4.0,.5)
udl=c2.number_input("Uniform load (kN/m)",0.0,100.0,10.0,1.0)
point=c3.number_input("Midspan point load (kN)",0.0,200.0,20.0,5.0)
reaction=(udl*span+point)/2
xx=[i*span/200 for i in range(201)]
shear=[reaction-udl*x-(point if x>=span/2 else 0) for x in xx]
moment=[reaction*x-udl*x*x/2-point*max(0,x-span/2) for x in xx]
figa,aa=plt.subplots(2,1,figsize=(9,5),sharex=True)
aa[0].plot(xx,shear); aa[0].axhline(0,lw=.8); aa[0].set_ylabel("Shear (kN)"); aa[0].grid(alpha=.25)
aa[1].plot(xx,moment); aa[1].axhline(0,lw=.8); aa[1].set_ylabel("Moment (kN·m)"); aa[1].set_xlabel("Span (m)"); aa[1].grid(alpha=.25); figa.tight_layout()
st.pyplot(figa,use_container_width=True)
st.write(f"**Idealized beam results:** each support reaction ≈ {reaction:.2f} kN; maximum sagging moment ≈ {max(moment):.2f} kN·m.")
st.caption("No full building load combinations, lateral analysis, stiffness model, foundation-soil interaction, deflection checks or complete code verification are included.")

st.header("4. Select an element to inspect")
register=pd.DataFrame(cols+beams+slabs+foundations)
category=st.radio("Choose element type",["Beam","Column","Slab","Foundation"],horizontal=True)
available=register[register.Type==category]
element_id=st.selectbox(f"Select {category} ID",available.ID.tolist())
el=available[available.ID==element_id].iloc[0]
left,right=st.columns(2)
with left:
    st.subheader(f"{element_id} — {category}")
    st.write(f"**Location:** {el.Location}")
    st.write(f"**Placeholder dimensions:** {el['Placeholder size']}")
    st.write("These values demonstrate selection and display only; they are not calculated design recommendations.")
with right:
    figd,ad=plt.subplots(figsize=(5,3))
    if category=="Beam":
        ad.add_patch(Rectangle((.12,.4),.76,.22,fill=False,lw=2)); ad.text(.5,.51,"Beam section",ha="center",va="center")
    elif category=="Column":
        ad.add_patch(Rectangle((.35,.2),.3,.6,fill=False,lw=2)); ad.text(.5,.5,"Column",ha="center",va="center",rotation=90)
    elif category=="Slab":
        ad.add_patch(Rectangle((.12,.42),.76,.12,fill=False,lw=2)); ad.text(.5,.48,"Slab thickness",ha="center",va="center")
    else:
        ad.add_patch(Rectangle((.2,.28),.6,.18,fill=False,lw=2)); ad.add_patch(Rectangle((.34,.46),.32,.22,fill=False,lw=2)); ad.text(.5,.37,"Footing",ha="center",va="center")
    ad.set_xlim(0,1); ad.set_ylim(0,1); ad.axis("off"); figd.tight_layout(); st.pyplot(figd,use_container_width=True)
st.dataframe(register,use_container_width=True,hide_index=True)
st.download_button("Download element register CSV",register.to_csv(index=False).encode(),"element_register.csv","text/csv")

st.header("5. Preliminary quantity and cost estimate")
total_area=footprint*selected
concrete=total_area*.20; steel=total_area*.035
items=pd.DataFrame([
 {"Item":"Concrete allowance","Quantity":round(concrete,2),"Unit":"m³","Rate ₹":7500,"Amount ₹":round(concrete*7500)},
 {"Item":"Steel allowance","Quantity":round(steel,2),"Unit":"tonne","Rate ₹":70000,"Amount ₹":round(steel*70000)},
 {"Item":"Masonry allowance","Quantity":round(total_area,2),"Unit":"m² floor-area basis","Rate ₹":1200,"Amount ₹":round(total_area*1200)},
 {"Item":"Finishing allowance","Quantity":round(total_area,2),"Unit":"m² floor-area basis","Rate ₹":1800,"Amount ₹":round(total_area*1800)}
])
st.dataframe(items,use_container_width=True,hide_index=True)
total=items["Amount ₹"].sum()
st.metric("Illustrative subtotal",f"₹{total:,.0f}")
st.caption("Area-based allowances only—not derived from verified member design or reinforcement detailing. Actual BOQ requires drawings, schedules, current local rates and professional quantity surveying.")

summary=f"""BUILDWISE AI — CONCEPTUAL PROJECT SUMMARY
Building type: {kind}
Location: {location}
Plot area: {area:.1f} m²
Assumed site coverage: {coverage:.0%} (placeholder)
Assumed FAR: {far:.2f} (placeholder)
Selected option: {floor_names[selected]}
Approx. footprint: {footprint:.1f} m²
Approx. total floor area: {total_area:.1f} m²
Conceptual footprint dimensions: {w:.2f} m × {d:.2f} m
Concrete allowance: {concrete:.2f} m³
Steel allowance: {steel:.2f} tonnes
Illustrative subtotal: ₹{total:,.0f}

Academic prototype only. Not construction-ready. Validate all planning rules, soil data, loads, dimensions, reinforcement, code provisions, quantities and costs with qualified professionals.
"""
st.download_button("Download project summary TXT",summary,"buildwise_project_summary.txt","text/plain")
with st.expander("Indian Standards and code implementation"):
    st.write("This prototype does not claim to implement or certify Indian Standards. A production system should encode verified provisions from the applicable editions of NBC and relevant IS codes for loads, RCC design, seismic design and foundations, with version tracking and unit-tested calculations. Location alone cannot replace a geotechnical investigation.")
