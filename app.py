import math
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BuildWise AI", page_icon="🏗️", layout="wide")

# BuildWise AI is an educational concept-design prototype. Outputs are not construction documents.
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.small-note {font-size: .88rem; color: #64748b;}
</style>
""", unsafe_allow_html=True)

st.title("🏗️ BuildWise AI")
st.caption("Building planning • coordinated concept layouts • member analysis • quantity and cost estimates")
st.warning(
    "Concept-design prototype only. It does not establish legal floor permission, soil capacity, or construction safety. "
    "Have the site data, structural model, calculations and drawings checked by qualified local professionals before construction."
)

# Only three project inputs. Geometry/engineering assumptions are shown in the results, not asked as required inputs.
with st.sidebar:
    st.header("Project inputs")
    location = st.text_input("Location", "Hyderabad, Telangana, India")
    plot_area = st.number_input("Plot area (m²)", min_value=30.0, max_value=5000.0, value=150.0, step=10.0)
    building_type = st.selectbox("Building type", ["Residential", "Commercial", "Mixed use", "Institutional"])
    st.divider()
    st.caption("These are the only project inputs. The prototype uses clearly stated geometry and loading assumptions.")

# ---------- geometry and option screening ----------
# Assumed near-rectangular plot geometry from area; not survey data.
plot_width = math.sqrt(plot_area / 1.5)
plot_length = plot_area / plot_width
# Placeholder coverage and setbacks: not locally verified.
coverage_assumption = 0.60
setback_assumption = 1.0
footprint = plot_area * coverage_assumption
approx_w = plot_width * math.sqrt(coverage_assumption)
approx_l = plot_length * math.sqrt(coverage_assumption)
floor_plate = min(footprint, max(20.0, (plot_width - 2*setback_assumption)*(plot_length - 2*setback_assumption)))
floor_plate = min(floor_plate, footprint)

# These are candidate options only; actual permissibility must be verified.
candidate_floors = [1, 2, 3, 4]
max_candidate = 4 if plot_area >= 120 else 3
options = [f for f in candidate_floors if f <= max_candidate]
option_labels = {1: "Ground floor", 2: "G+1 (2 floors)", 3: "G+2 (3 floors)", 4: "G+3 (4 floors)"}

st.subheader("1. Site assessment and floor options")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Plot area", f"{plot_area:,.1f} m²")
c2.metric("Assumed plot shape", f"{plot_width:.1f} × {plot_length:.1f} m")
c3.metric("Concept footprint", f"{floor_plate:.1f} m²")
c4.metric("Location", location[:28] + ("…" if len(location) > 28 else ""))

st.info(
    "The plot dimensions are an estimated near-rectangular geometry derived from area, not a surveyed boundary. "
    "Coverage and setback values below are demo assumptions, not verified rules for the entered location."
)
# Location-aware rule-source screening. A typed location is not enough to certify plot-specific compliance.
loc_lower = location.lower()
if any(token in loc_lower for token in ["telangana", "hyderabad", "secunderabad"]):
    region_label = "Telangana — likely relevant state framework"
    planning_source = "TG-bPASS / BuildNow official rule and GO portals"
    planning_url = "https://buildnow.telangana.gov.in/go-and-act/"
    planning_status = "Official source identified; exact authority/zone and plot conditions still need checking"
else:
    region_label = "Region not confidently resolved"
    planning_source = "Identify the applicable municipal/development authority"
    planning_url = ""
    planning_status = "Location-specific rule source not yet confirmed"

rules_df = pd.DataFrame([
    ["Location / jurisdiction", region_label, planning_status],
    ["Plot geometry", f"{plot_width:.2f} m × {plot_length:.2f} m", "Estimated from area only; survey dimensions required"],
    ["Coverage used in concept", f"{coverage_assumption*100:.0f}%", "Illustrative assumption — not a compliance result"],
    ["Setback used in concept", f"{setback_assumption:.1f} m each side", "Illustrative assumption — verify road width, zone and plot conditions"],
    ["Soil bearing capacity", "Unknown", "Site-specific geotechnical report required"],
    ["FAR/FSI / height / fire limits", "Not calculated as compliant", "Requires applicable rule, plot/road/zone details and authority review"],
], columns=["Assessment item", "Prototype value", "Status"])
st.dataframe(rules_df, use_container_width=True, hide_index=True)
if planning_url:
    st.markdown(f"**Regional rules source:** [{planning_source}]({planning_url})")
else:
    st.markdown(f"**Regional rules source:** {planning_source}")

st.markdown("#### Code-based screening and approval readiness")
st.warning(
    "This dashboard can show preliminary checks and missing evidence; it cannot issue statutory building approval or certify structural safety. "
    "A result is marked 'screened' only when the required data and calculation are actually available. The current three-input prototype does not contain enough site or structural data to approve the building."
)
code_framework_df = pd.DataFrame([
    ["Architectural/site planning", "Applicable state/local building rules and current amendments", "Source lookup only; exact plot zoning and road width not entered"],
    ["RCC member design", "IS 456 (plain and reinforced concrete)", "Not verified — complete member geometry, reinforcement, materials, and load combinations required"],
    ["Dead and imposed loads", "IS 875 Parts 1 and 2", "Simplified load assumptions; occupancy-specific loads need verification"],
    ["Wind loads", "IS 875 Part 3", "Not verified — site exposure, height and building parameters required"],
    ["Earthquake design", "Applicable current IS 1893 provisions and related detailing standards", "Not verified — seismic parameters and complete structural model required"],
    ["Soil investigation / foundations", "IS 1892 and IS 1904; relevant foundation standards", "Not verified — geotechnical report and foundation design checks required"],
], columns=["Check area", "Relevant code framework", "Current app status"])
st.dataframe(code_framework_df, use_container_width=True, hide_index=True)

st.markdown("**Candidate floor options**")
option_df = pd.DataFrame([
    {"Option": option_labels[f], "Floors": f, "Indicative total floor area (m²)": round(floor_plate*f, 1),
     "Status": "Candidate only — feasibility checks required"}
    for f in options
])
st.dataframe(option_df, use_container_width=True, hide_index=True)
chosen_floors = st.radio(
    "Choose an option to develop",
    options=options,
    format_func=lambda f: option_labels[f],
    horizontal=True,
    key="floor_option"
)
total_area = floor_plate * chosen_floors

# ---------- architectural floor plan ----------
def room_plan(floor_idx, width, length, btype):
    """Generate a responsive, building-type-specific architectural concept plan.

    Room placement is selected from different adjacency templates by building use,
    storey, footprint area and aspect ratio. Geometry is approximate, not surveyed.
    """
    from matplotlib.patches import Rectangle, Arc, Circle

    w, L = max(float(width), 6.0), max(float(length), 6.0)
    area = w * L
    aspect = w / L
    floor_idx = int(max(0, min(floor_idx, 3)))
    ink, secondary, furniture, window_color, door_color = "#111827", "#475569", "#64748b", "#0284c7", "#7c3aed"

    # Each template is a genuinely different room-adjacency arrangement.
    # Coordinates are normalized (0..1), then scaled to the generated footprint.
    if btype == "Residential":
        if floor_idx == 0:
            template = [
                (.00,.52,.34,1.00,"BEDROOM 1","bed"), (.34,.52,.66,1.00,"KITCHEN","kitchen"),
                (.66,.72,1.00,1.00,"BATH / WC","bath"), (.66,.52,1.00,.72,"UTILITY","plain"),
                (.00,.00,.48,.52,"LIVING ROOM","living"), (.48,.00,.76,.52,"DINING","dining"),
                (.76,.00,1.00,.52,"STAIRCASE","stair")]
        else:
            template = [
                (.00,.55,.36,1.00,f"BEDROOM {min(floor_idx+1,4)}","bed"), (.36,.55,.68,1.00,"BEDROOM / STUDY","bed"),
                (.68,.76,1.00,1.00,"BATH / WC","bath"), (.68,.55,1.00,.76,"LINEN / STORE","plain"),
                (.00,.00,.43,.55,"FAMILY LOUNGE","living"), (.43,.00,.73,.55,"MASTER BEDROOM","bed"),
                (.73,.00,1.00,.55,"STAIR / LANDING","stair")]
    elif btype == "Commercial":
        if floor_idx == 0:
            template = [
                (.00,.56,.27,1.00,"SHOP / OFFICE 1","plain"), (.27,.56,.70,1.00,"OPEN WORK / SALES","work"),
                (.70,.76,1.00,1.00,"TOILET","bath"), (.70,.56,1.00,.76,"STORE","plain"),
                (.00,.00,.24,.56,"RECEPTION","work"), (.24,.00,.70,.56,"CUSTOMER / WORK AREA","work"),
                (.70,.00,1.00,.56,"STAIR / LOBBY","stair")]
        else:
            template = [
                (.00,.58,.33,1.00,"PRIVATE OFFICE","work"), (.33,.58,.70,1.00,"MEETING ROOM","table"),
                (.70,.77,1.00,1.00,"TOILET","bath"), (.70,.58,1.00,.77,"RECORDS / STORE","plain"),
                (.00,.00,.22,.58,"RECEPTION","work"), (.22,.00,.70,.58,"OPEN OFFICE","work"),
                (.70,.00,1.00,.58,"STAIR / LOBBY","stair")]
    elif btype == "Institutional":
        if floor_idx == 0:
            template = [
                (.00,.55,.36,1.00,"CLASSROOM 1","table"), (.36,.55,.72,1.00,"CLASSROOM 2","table"),
                (.72,.76,1.00,1.00,"TOILET","bath"), (.72,.55,1.00,.76,"STORE","plain"),
                (.00,.00,.28,.55,"OFFICE","work"), (.28,.00,.72,.55,"ACTIVITY / COMMON HALL","table"),
                (.72,.00,1.00,.55,"STAIR / LOBBY","stair")]
        else:
            template = [
                (.00,.58,.34,1.00,"CLASSROOM 3","table"), (.34,.58,.70,1.00,"CLASSROOM 4","table"),
                (.70,.77,1.00,1.00,"TOILET","bath"), (.70,.58,1.00,.77,"STORE","plain"),
                (.00,.00,.25,.58,"STAFF ROOM","work"), (.25,.00,.70,.58,"ACTIVITY HALL","table"),
                (.70,.00,1.00,.58,"STAIR / LOBBY","stair")]
    else:  # Mixed use: commercial frontage at ground, residential above.
        if floor_idx == 0:
            template = [
                (.00,.56,.36,1.00,"SHOP / OFFICE","work"), (.36,.56,.68,1.00,"KITCHEN","kitchen"),
                (.68,.76,1.00,1.00,"BATH / WC","bath"), (.68,.56,1.00,.76,"UTILITY","plain"),
                (.00,.00,.48,.56,"SHOP / LIVING","living"), (.48,.00,.73,.56,"DINING","dining"),
                (.73,.00,1.00,.56,"STAIRCASE","stair")]
        else:
            template = [
                (.00,.55,.36,1.00,"BEDROOM 1","bed"), (.36,.55,.68,1.00,"KITCHEN","kitchen"),
                (.68,.76,1.00,1.00,"BATH / WC","bath"), (.68,.55,1.00,.76,"STORE","plain"),
                (.00,.00,.43,.55,"FAMILY LOUNGE","living"), (.43,.00,.73,.55,"BEDROOM 2","bed"),
                (.73,.00,1.00,.55,"STAIR / LANDING","stair")]

    # Upper storeys should not all repeat the same drawing. Re-arrange the upper-floor
    # template for higher levels while preserving room types and the same footprint.
    if floor_idx == 2:
        template = [(1-x1, 1-y1, 1-x0, 1-y0, name, kind)
                    for x0,y0,x1,y1,name,kind in template]
    elif floor_idx >= 3:
        template = [(1-x1, y0, 1-x0, y1, name, kind)
                    for x0,y0,x1,y1,name,kind in template]

    # For a portrait footprint, rotate the normalized plan so the long direction is used efficiently.
    if aspect < 0.82:
        template = [(y0, x0, y1, x1, name, kind) for x0,y0,x1,y1,name,kind in template]
        # Rotation changes the normalized dimensions; map the drawing to its actual footprint.
        def xy(u, v): return (u*w, v*L)
    else:
        def xy(u, v): return (u*w, v*L)

    fig, ax = plt.subplots(figsize=(12, 9), dpi=190)
    fig.patch.set_facecolor("white")
    ax.set_aspect("equal")
    ax.set_xlim(-2.0, w+2.2); ax.set_ylim(-2.55, L+2.4); ax.axis("off")
    # Heavy exterior wall and inner face.
    wall = min(.20, w*.018, L*.018)
    ax.add_patch(Rectangle((0,0),w,L,fill=False,ec=ink,lw=3.0,zorder=3))
    ax.add_patch(Rectangle((wall,wall),w-2*wall,L-2*wall,fill=False,ec=ink,lw=.8,zorder=3))

    rooms=[]
    for x0,y0,x1,y1,name,kind in template:
        xa,ya=xy(x0,y0); xb,yb=xy(x1,y1)
        xa,xb=sorted((xa,xb)); ya,yb=sorted((ya,yb))
        rooms.append((xa,ya,xb,yb,name,kind))
        # Each room tile is bounded by clear CAD-style partition lines.
        if x0 > 0.001: ax.plot([xa,xa],[ya,yb],color=ink,lw=1.35,zorder=3)
        if x1 < 0.999: ax.plot([xb,xb],[ya,yb],color=ink,lw=1.35,zorder=3)
        if y0 > 0.001: ax.plot([xa,xb],[ya,ya],color=ink,lw=1.35,zorder=3)
        if y1 < 0.999: ax.plot([xa,xb],[yb,yb],color=ink,lw=1.35,zorder=3)
        rw,rh=xb-xa,yb-ya
        # Wrap long room names to the actual room width so labels never spill into adjacent rooms.
        import textwrap
        chars_per_line = max(7, min(20, int(rw * 4.2)))
        room_name = "\n".join(textwrap.wrap(name, width=chars_per_line, break_long_words=False))
        dims = f"{rw:.2f} × {rh:.2f} m  |  {rw*rh:.1f} m²"
        fs = 4.0 if min(rw, rh) < 1.8 else (4.7 if rw < 2.6 else 5.3)
        # Compact centered labels; keep a clear furniture zone below them.
        label_y = yb - min(.16, rh*.09)
        ax.text((xa+xb)/2, label_y, room_name, ha="center", va="top", fontsize=fs,
                linespacing=0.92, color=ink, fontweight="bold", zorder=7,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.35, alpha=0.94))
        ax.text((xa+xb)/2, label_y-min(.22, rh*.13), dims, ha="center", va="top", fontsize=max(3.4, fs-.5),
                color=secondary, zorder=7,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.2, alpha=0.94))
        # Furniture is drawn lower in each room, leaving labels readable and unobstructed.
        cx,cy=(xa+xb)/2, ya+rh*.38
        if kind == "bed":
            bw,bh=min(rw*.48,1.65),min(rh*.48,1.95)
            ax.add_patch(Rectangle((cx-bw/2,cy-bh/2),bw,bh,fill=False,ec=furniture,lw=1.0,zorder=5))
            # Headboard and two pillows make the bed symbol recognizable.
            ax.plot([cx-bw/2,cx+bw/2],[cy+bh*.27,cy+bh*.27],color=furniture,lw=.8,zorder=5)
            pw,ph=bw*.27,bh*.15
            for px in (cx-bw*.23,cx+bw*.23):
                ax.add_patch(Rectangle((px-pw/2,cy+bh*.34-ph/2),pw,ph,fill=False,ec=furniture,lw=.65,zorder=5))
            # Two bedside tables and a wardrobe, scaled to fit the room.
            side=min(.34,max(.20,rw*.10)); side_h=min(.34,max(.20,rh*.10))
            for sx in (cx-bw/2-side*.65, cx+bw/2+side*.65):
                if xa+.08 < sx-side/2 and sx+side/2 < xb-.08:
                    ax.add_patch(Rectangle((sx-side/2,cy+bh*.15-side_h/2),side,side_h,fill=False,ec=furniture,lw=.7,zorder=5))
            ww,wh=min(.95,rw*.30),min(.30,rh*.12)
            ax.add_patch(Rectangle((cx-ww/2,ya+rh*.08),ww,wh,fill=False,ec=furniture,lw=.8,zorder=5))
            ax.plot([cx,cx],[ya+rh*.08,ya+rh*.08+wh],color=furniture,lw=.55,zorder=5)
            if rw > 2.7:
                ax.add_patch(Rectangle((xa+rw*.08,cy-rh*.32),min(.65,rw*.22),min(.35,rh*.12),fill=False,ec=furniture,lw=.7,zorder=5)) # study desk
        elif kind == "living":
            sw,sh=min(rw*.56,2.0),min(rh*.20,.62)
            ax.add_patch(Rectangle((cx-sw/2,cy-sh/2),sw,sh,fill=False,ec=furniture,lw=1.0,zorder=5))
            ax.plot([cx-sw*.28,cx-sw*.28],[cy-sh/2,cy+sh/2],color=furniture,lw=.7,zorder=5)
            ax.plot([cx+sw*.28,cx+sw*.28],[cy-sh/2,cy+sh/2],color=furniture,lw=.7,zorder=5)
            # Coffee table opposite the sofa.
            tw,th=min(rw*.28,.8),min(rh*.15,.42)
            ax.add_patch(Rectangle((cx-tw/2,cy-rh*.18-th/2),tw,th,fill=False,ec=furniture,lw=.8,zorder=5))
            # Accent chairs and a TV/media console complete the seating group.
            cw,ch=min(.68,rw*.20),min(.52,rh*.16)
            for sx in (cx-sw*.36-cw*.40, cx+sw*.36+cw*.40):
                if xa+.08 < sx-cw/2 and sx+cw/2 < xb-.08:
                    ax.add_patch(Rectangle((sx-cw/2,cy-rh*.34-ch/2),cw,ch,fill=False,ec=furniture,lw=.8,zorder=5))
            tvw,tvh=min(1.15,rw*.38),min(.16,rh*.07)
            ax.add_patch(Rectangle((cx-tvw/2,ya+rh*.08),tvw,tvh,fill=False,ec=furniture,lw=.8,zorder=5))
        elif kind in ("work", "plain"):
            # Desk/counter and chair for offices, stores and flexible rooms.
            dw,dh=min(rw*.48,1.45),min(rh*.16,.48)
            ax.add_patch(Rectangle((cx-dw/2,cy+rh*.06),dw,dh,fill=False,ec=furniture,lw=.9,zorder=5))
            ax.add_patch(Rectangle((cx-.16,cy-rh*.12),.32,.28,fill=False,ec=furniture,lw=.75,zorder=5))
            # Storage/bookshelf and a second visitor chair for larger rooms.
            shelf_w,shelf_h=min(.22,rw*.08),min(.85,rh*.30)
            ax.add_patch(Rectangle((xa+rw*.08,cy-shelf_h/2),shelf_w,shelf_h,fill=False,ec=furniture,lw=.75,zorder=5))
            for k in (1,2,3):
                yy=cy-shelf_h/2+shelf_h*k/4
                ax.plot([xa+rw*.08,xa+rw*.08+shelf_w],[yy,yy],color=furniture,lw=.5,zorder=5)
            if rw > 2.5 and rh > 2.5:
                ax.add_patch(Rectangle((cx+.30,cy-rh*.27),.30,.27,fill=False,ec=furniture,lw=.7,zorder=5))
        elif kind in ("dining","table"):
            bw,bh=min(rw*.34,1.15),min(rh*.25,.82)
            ax.add_patch(Rectangle((cx-bw/2,cy-bh/2),bw,bh,fill=False,ec=furniture,lw=1.0,zorder=5))
            # Four chairs around the table when the room has enough space.
            if rw > 2.1 and rh > 2.1:
                chair=.18
                for px,py in ((cx-bw*.30,cy-bh/2-.15),(cx+bw*.30,cy-bh/2-.15),
                              (cx-bw*.30,cy+bh/2+.15),(cx+bw*.30,cy+bh/2+.15),
                              (cx-bw/2-.15,cy),(cx+bw/2+.15,cy)):
                    ax.add_patch(Rectangle((px-chair/2,py-chair/2),chair,chair,fill=False,ec=furniture,lw=.7,zorder=5))
        elif kind == "kitchen":
            counter_h=min(.24,rh*.10)
            ax.add_patch(Rectangle((xa+.12,ya+rh*.20),max(.25,rw-.24),counter_h,fill=False,ec=furniture,lw=.9,zorder=5))
            # Sink and hob symbols along the counter.
            ax.add_patch(Rectangle((xa+.22,ya+rh*.21),min(.38,rw*.18),counter_h*.65,fill=False,ec=furniture,lw=.6,zorder=5))
            for dx in (xa+rw*.68,xa+rw*.78):
                ax.add_patch(Circle((dx,ya+rh*.25),radius=min(.055,rw*.025,rh*.025),fill=False,ec=furniture,lw=.65,zorder=5))
            # Refrigerator and a compact prep/island counter where room size permits.
            fw,fh=min(.42,rw*.16),min(.58,rh*.22)
            ax.add_patch(Rectangle((xb-fw-.10,ya+rh*.12),fw,fh,fill=False,ec=furniture,lw=.8,zorder=5))
            ax.plot([xb-fw-.10,xb-.10],[ya+rh*.12+fh*.72,ya+rh*.12+fh*.72],color=furniture,lw=.5,zorder=5)
            if rw > 2.8 and rh > 2.7:
                iw,ih=min(.85,rw*.30),min(.30,rh*.11)
                ax.add_patch(Rectangle((cx-iw/2,ya+rh*.52),iw,ih,fill=False,ec=furniture,lw=.8,zorder=5))
        elif kind == "bath":
            bw=min(.52,max(.24,rw*.25)); bh=min(.34,max(.22,rh*.16))
            ax.add_patch(Rectangle((xa+.12,ya+rh*.22),bw,bh,fill=False,ec=furniture,lw=.8,zorder=5)) # shower
            ax.add_patch(Circle((xa+rw*.70,ya+rh*.30),radius=min(.12,rw*.07,rh*.07),fill=False,ec=furniture,lw=.8,zorder=5)) # basin
            ax.add_patch(Rectangle((xa+rw*.62,ya+rh*.48),min(.28,rw*.16),min(.38,rh*.18),fill=False,ec=furniture,lw=.8,zorder=5)) # WC
            # Small vanity and towel/storage cabinet.
            ax.add_patch(Rectangle((xa+rw*.60,ya+rh*.18),min(.42,rw*.20),min(.20,rh*.09),fill=False,ec=furniture,lw=.7,zorder=5))
            ax.add_patch(Rectangle((xb-min(.22,rw*.10)-.08,yb-min(.60,rh*.24)-.08),min(.22,rw*.10),min(.60,rh*.24),fill=False,ec=furniture,lw=.7,zorder=5))
        elif kind == "stair":
            for k in range(1,8):
                yy=ya+rh*k/8
                ax.plot([xa+.12,xb-.12],[yy,yy],color=furniture,lw=.5,zorder=5)
            ax.annotate("UP",xy=(cx,yb-.12),xytext=(cx,ya+.12),arrowprops=dict(arrowstyle="->",lw=.7,color=furniture),ha="center",va="center",fontsize=6,color=furniture,zorder=6)

    # Draw internal door openings at shared room partitions. These are schematic
    # swing symbols; the white gap visually interrupts the partition and the arc shows swing.
    seen_doors = set()
    door_w = min(.82, max(.68, min(w, L)*.10))
    for i, r1 in enumerate(rooms):
        ax1, ay1, bx1, by1, n1, k1 = r1
        for r2 in rooms[i+1:]:
            ax2, ay2, bx2, by2, n2, k2 = r2
            # Shared vertical wall
            shared_x = None
            if abs(bx1-ax2) < .015: shared_x = bx1
            elif abs(bx2-ax1) < .015: shared_x = bx2
            if shared_x is not None:
                lo, hi = max(ay1,ay2), min(by1,by2)
                if hi-lo > door_w+.15:
                    cy_d = (lo+hi)/2
                    key=('v',round(shared_x,2),round(cy_d,2))
                    if key not in seen_doors:
                        seen_doors.add(key)
                        ax.plot([shared_x,shared_x],[cy_d-door_w/2,cy_d+door_w/2],color='white',lw=3.2,zorder=8)
                        ax.plot([shared_x,shared_x+door_w*.72],[cy_d-door_w/2,cy_d-door_w/2],color=door_color,lw=.75,zorder=9)
                        ax.add_patch(Arc((shared_x,cy_d-door_w/2),door_w,door_w,theta1=0,theta2=90,ec=door_color,lw=.7,zorder=9))
            # Shared horizontal wall
            shared_y = None
            if abs(by1-ay2) < .015: shared_y = by1
            elif abs(by2-ay1) < .015: shared_y = by2
            if shared_y is not None:
                lo, hi = max(ax1,ax2), min(bx1,bx2)
                if hi-lo > door_w+.15:
                    cx_d = (lo+hi)/2
                    key=('h',round(cx_d,2),round(shared_y,2))
                    if key not in seen_doors:
                        seen_doors.add(key)
                        ax.plot([cx_d-door_w/2,cx_d+door_w/2],[shared_y,shared_y],color='white',lw=3.2,zorder=8)
                        ax.plot([cx_d-door_w/2,cx_d-door_w/2],[shared_y,shared_y+door_w*.72],color=door_color,lw=.75,zorder=9)
                        ax.add_patch(Arc((cx_d-door_w/2,shared_y),door_w,door_w,theta1=0,theta2=90,ec=door_color,lw=.7,zorder=9))

    # Main entrance and exterior windows. These are schematic opening markers, not construction details.
    ew=min(.95,max(.70,w*.075)); ex=w*.20
    ax.plot([ex-ew/2,ex+ew/2],[0,0],color="white",lw=4.5,zorder=8)
    ax.plot([ex-ew/2,ex-ew/2],[0,ew],color=door_color,lw=.8,zorder=9)
    ax.add_patch(Arc((ex-ew/2,0),2*ew,2*ew,theta1=0,theta2=90,ec=door_color,lw=.7,zorder=9))
    for yy in (L*.22,L*.78):
        for xx,sgn in ((0,1),(w,-1)):
            ax.plot([xx,xx],[yy-.38,yy+.38],color="white",lw=4.2,zorder=8)
            ax.plot([xx+sgn*wall*.25,xx+sgn*wall*.25],[yy-.38,yy+.38],color=window_color,lw=.9,zorder=9)
            ax.plot([xx-sgn*wall*.25,xx-sgn*wall*.25],[yy-.38,yy+.38],color=window_color,lw=.9,zorder=9)

    # Overall and chained dimensions tied to actual template divisions.
    def hdim(xa,xb,y,label,base):
        ax.plot([xa,xa],[base,y],color=secondary,lw=.4); ax.plot([xb,xb],[base,y],color=secondary,lw=.4)
        ax.annotate("",xy=(xa,y),xytext=(xb,y),arrowprops=dict(arrowstyle="<->",lw=.6,color=secondary))
        ax.text((xa+xb)/2,y+.07,label,ha="center",va="bottom",fontsize=6.5,color=secondary)
    def vdim(ya,yb,x,label,base):
        ax.plot([base,x],[ya,ya],color=secondary,lw=.4); ax.plot([base,x],[yb,yb],color=secondary,lw=.4)
        ax.annotate("",xy=(x,ya),xytext=(x,yb),arrowprops=dict(arrowstyle="<->",lw=.6,color=secondary))
        ax.text(x-.07,(ya+yb)/2,label,rotation=90,ha="right",va="center",fontsize=6.5,color=secondary)
    hdim(0,w,L+1.25,f"{w:.2f} m",L)
    vdim(0,L,-1.2,f"{L:.2f} m",0)
    # First-level partitions on the top and left edges provide meaningful chained dimensions.
    xs=sorted(set(round(v*w,3) for room in template for v in (room[0],room[2]) if 0<v<1))
    ys=sorted(set(round(v*L,3) for room in template for v in (room[1],room[3]) if 0<v<1))
    chain=[0]+xs+[w]
    for a,b in zip(chain,chain[1:]): hdim(a,b,L+.65,f"{b-a:.2f}",L)
    ychain=[0]+ys+[L]
    # Limit crowded side-chain labels for very small footprints.
    if len(ychain)<=6:
        for a,b in zip(ychain,ychain[1:]): vdim(a,b,-.62,f"{b-a:.2f}",0)
    ax.annotate("N",xy=(w+.8,L-.2),xytext=(w+.8,L-.9),arrowprops=dict(arrowstyle="-|>",lw=1,color=ink),ha="center",fontsize=9,fontweight="bold")
    bar=min(2.0,w*.3); ax.plot([0,bar],[-1.22,-1.22],color=ink,lw=2)
    ax.text(bar/2,-1.35,f"Scale bar {bar:.1f} m",ha="center",va="top",fontsize=6,color=secondary)
    ax.add_patch(Rectangle((-1.75,-2.3),w+3.65,L+4.2,fill=False,ec="#9ca3af",lw=.65,zorder=0))
    ax.text(0,-1.83,"BUILDWISE AI  |  ARCHITECTURAL CONCEPT",ha="left",va="center",fontsize=7.2,color=ink,fontweight="bold")
    ax.text(0,-2.08,f"PROJECT: {btype.upper()}   DRAWING: A-{floor_idx+1:02d}   UNITS: METRES",ha="left",va="center",fontsize=5.8,color=secondary)
    title=["GROUND FLOOR PLAN","FIRST FLOOR PLAN","SECOND FLOOR PLAN","THIRD FLOOR PLAN"][floor_idx]
    ax.text(w,-1.83,f"{title}  |  NOT FOR CONSTRUCTION",ha="right",va="center",fontsize=6,color=secondary,fontweight="bold")
    ax.text(w,-2.08,f"APPROX. FLOOR AREA: {area:.1f} m²   SCALE: SCHEMATIC",ha="right",va="center",fontsize=5.8,color=secondary)
    ax.set_title(f"ARCHITECTURAL FLOOR PLAN — {title}",fontsize=11,pad=16,color=ink,fontweight="bold")
    fig.tight_layout(pad=1.0)
    return fig

st.subheader("2. Architectural plans — every selected floor")
st.caption("Architectural concept sheets with room dimensions and approximate areas, partition-based dimension chains, wall hierarchy, door/window symbols, furniture, stair direction, north arrow, and a drawing title block. These remain schematic concept plans; actual surveyed geometry, room requirements, openings, services, ventilation/daylight and local rules require architectural coordination.")
tabs = st.tabs([("Ground floor" if i == 0 else f"Floor {i+1}") for i in range(chosen_floors)])
for i, tab in enumerate(tabs):
    with tab:
        fig = room_plan(i, approx_w, approx_l, building_type)
        st.pyplot(fig, use_container_width=True)
        st.download_button(
            f"Download floor {i+1} plan (PNG)",
            data=(lambda f: (lambda b: (f.savefig(b, format="png", dpi=180, bbox_inches="tight"), b.getvalue())[1])(BytesIO()))(fig),
            file_name=f"architectural_floor_{i+1}.png",
            mime="image/png",
            key=f"download_plan_{i}"
        )
        pdf_buffer = BytesIO()
        fig.savefig(pdf_buffer, format="pdf", bbox_inches="tight")
        st.download_button(
            f"Download floor {i+1} plan (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=f"architectural_floor_{i+1}.pdf",
            mime="application/pdf",
            key=f"download_plan_pdf_{i}"
        )
        plt.close(fig)

# ---------- coordinated concept structural grid ----------
# Structural grid adapts to the generated footprint instead of always using
# the same 4-column by 3-row arrangement. Bay spacing is only a concept target.
span_target = 4.0
nx_bays = max(2, min(6, int(math.ceil(approx_w / span_target))))
ny_bays = max(2, min(6, int(math.ceil(approx_l / span_target))))
grid_x = np.linspace(0.0, approx_w, nx_bays + 1).tolist()
grid_y = np.linspace(0.0, approx_l, ny_bays + 1).tolist()
columns = []
beams = []
slabs = []
footings = []
for j, y in enumerate(grid_y):
    for i, x in enumerate(grid_x):
        columns.append({"id": f"C{j*len(grid_x)+i+1}", "x": x, "y": y, "floor": "All floors"})
for j, y in enumerate(grid_y):
    for i in range(len(grid_x)-1):
        beams.append({"id": f"B{j*(len(grid_x)-1)+i+1}", "x1": grid_x[i], "y1": y, "x2": grid_x[i+1], "y2": y, "span": grid_x[i+1]-grid_x[i], "orientation": "Horizontal"})
for j in range(len(grid_y)-1):
    for i in range(len(grid_x)):
        beams.append({"id": f"B{len(grid_y)*(len(grid_x)-1)+j*len(grid_x)+i+1}", "x1": grid_x[i], "y1": grid_y[j], "x2": grid_x[i], "y2": grid_y[j+1], "span": grid_y[j+1]-grid_y[j], "orientation": "Vertical"})
for j in range(len(grid_y)-1):
    for i in range(len(grid_x)-1):
        slabs.append({"id": f"S{j*(len(grid_x)-1)+i+1}", "x1": grid_x[i], "y1": grid_y[j], "x2": grid_x[i+1], "y2": grid_y[j+1]})
for i, c in enumerate(columns):
    footings.append({"id": f"F{i+1}", "column": c["id"], "x": c["x"], "y": c["y"]})

# ---------- RCC layout: conceptual beam/column/slab/foundation grid ----------
st.subheader("3. RCC structural layout")
st.caption("Conceptual RCC framing layout generated from the prototype grid. Select a storey to view beam, column and slab labels; switch to foundation layout to view footing positions. This is a schematic coordination diagram, not a construction drawing or verified structural design.")
rcc_view = st.radio("RCC layout view", ["Floor framing layout", "Foundation layout"], horizontal=True, key="rcc_layout_view")
rcc_floor = st.selectbox("Storey", ["All typical floors"] + ["Ground floor" if i == 0 else f"Floor {i+1}" for i in range(chosen_floors)], key="rcc_floor")
fig_rcc, ax_rcc = plt.subplots(figsize=(10, 7))
ax_rcc.set_aspect("equal")
ax_rcc.set_facecolor("white")
if rcc_view == "Floor framing layout":
    # Slab panels
    for sl in slabs:
        ax_rcc.add_patch(Rectangle((sl["x1"], sl["y1"]), sl["x2"]-sl["x1"], sl["y2"]-sl["y1"], facecolor="#e0f2fe", edgecolor="none", alpha=0.8))
        ax_rcc.text((sl["x1"]+sl["x2"])/2, (sl["y1"]+sl["y2"])/2, sl["id"], ha="center", va="center", fontsize=9, color="#075985", fontweight="bold")
    # Beam centre lines and IDs
    for b in beams:
        ax_rcc.plot([b["x1"], b["x2"]], [b["y1"], b["y2"]], color="#2563eb", linewidth=2.2, zorder=3)
        mx, my = (b["x1"]+b["x2"])/2, (b["y1"]+b["y2"])/2
        ax_rcc.text(mx, my+0.12, b["id"], fontsize=7.5, color="#1d4ed8", ha="center", va="bottom")
    # Column markers
    for c in columns:
        ax_rcc.add_patch(Rectangle((c["x"]-0.12, c["y"]-0.12), 0.24, 0.24, facecolor="#b91c1c", edgecolor="#7f1d1d", linewidth=0.8, zorder=5))
        ax_rcc.text(c["x"]+0.16, c["y"]+0.15, c["id"], fontsize=7.5, color="#991b1b", fontweight="bold")
    ax_rcc.set_title(f"RCC FLOOR FRAMING — {rcc_floor.upper()}", fontsize=12, fontweight="bold")
    ax_rcc.set_xlabel("Grid dimension (m)")
    ax_rcc.set_ylabel("Grid dimension (m)")
    ax_rcc.legend(handles=[plt.Line2D([0],[0], color="#2563eb", lw=2, label="Beam centre line"), plt.Line2D([0],[0], marker="s", color="w", markerfacecolor="#b91c1c", markersize=8, label="Column"), Rectangle((0,0),1,1,facecolor="#e0f2fe", label="Slab panel")], loc="upper center", bbox_to_anchor=(0.5,-0.12), ncol=3, frameon=False)
else:
    for f in footings:
        size = 0.65
        ax_rcc.add_patch(Rectangle((f["x"]-size/2, f["y"]-size/2), size, size, facecolor="#fef3c7", edgecolor="#b45309", linewidth=1.6))
        ax_rcc.add_patch(Rectangle((f["x"]-0.12, f["y"]-0.12), 0.24, 0.24, facecolor="#b91c1c", edgecolor="#7f1d1d", linewidth=0.8))
        ax_rcc.text(f["x"], f["y"]+0.43, f["id"], fontsize=7.5, color="#92400e", ha="center", fontweight="bold")
        ax_rcc.text(f["x"]+0.16, f["y"]-0.22, f["column"], fontsize=6.5, color="#991b1b")
    ax_rcc.set_title("RCC FOUNDATION / FOOTING POSITION PLAN", fontsize=12, fontweight="bold")
    ax_rcc.set_xlabel("Grid dimension (m)")
    ax_rcc.set_ylabel("Grid dimension (m)")
ax_rcc.set_xlim(-0.6, approx_w+0.8)
ax_rcc.set_ylim(-0.6, approx_l+0.8)
ax_rcc.grid(True, linestyle=":", linewidth=0.5, alpha=0.35)
fig_rcc.tight_layout()
st.pyplot(fig_rcc, use_container_width=True)
rcc_buffer = BytesIO()
fig_rcc.savefig(rcc_buffer, format="pdf", bbox_inches="tight")
st.download_button("Download RCC layout (PDF)", data=rcc_buffer.getvalue(), file_name="buildwise_rcc_layout_concept.pdf", mime="application/pdf")
plt.close(fig_rcc)
with st.expander("RCC member schedule"):
    st.markdown("**Columns**")
    st.dataframe(pd.DataFrame(columns), use_container_width=True, hide_index=True)
    st.markdown("**Beams**")
    st.dataframe(pd.DataFrame(beams), use_container_width=True, hide_index=True)
    st.markdown("**Slab panels**")
    st.dataframe(pd.DataFrame(slabs), use_container_width=True, hide_index=True)
    st.markdown("**Footings**")
    st.dataframe(pd.DataFrame(footings), use_container_width=True, hide_index=True)

# ---------- dedicated load analysis and structural analysis sections ----------
st.subheader("4. Load analysis")
st.caption(
    "Preliminary load ledger for learning and prototype demonstration. Loads below use stated assumptions; "
    "they are not a substitute for a complete load take-down or code-based building model."
)
load_dead_slab = 0.15 * 25.0                 # 150 mm trial slab x 25 kN/m³
load_floor_finish = 1.0                     # kN/m² allowance
load_wall_allowance = 1.0                   # kN/m² allowance, not wall-by-wall take-down
load_live = 2.0 if building_type in ["Residential", "Mixed use"] else 3.0
load_dead_total = load_dead_slab + load_floor_finish + load_wall_allowance
load_service_area = load_dead_total + load_live
load_rows = [
    {"Load component": "RCC slab self-weight (150 mm trial)", "Assumption / basis": "0.15 m × 25 kN/m³", "Load (kN/m²)": load_dead_slab},
    {"Load component": "Floor finish allowance", "Assumption / basis": "Assumed allowance", "Load (kN/m²)": load_floor_finish},
    {"Load component": "Wall / partition allowance", "Assumption / basis": "Preliminary allowance; not wall-by-wall", "Load (kN/m²)": load_wall_allowance},
    {"Load component": "Imposed / live load", "Assumption / basis": "Illustrative occupancy allowance", "Load (kN/m²)": load_live},
    {"Load component": "Total dead load allowance", "Assumption / basis": "Slab + finish + wall allowance", "Load (kN/m²)": load_dead_total},
    {"Load component": "Total service area load", "Assumption / basis": "Dead + live; preliminary", "Load (kN/m²)": load_service_area},
]
st.dataframe(pd.DataFrame(load_rows), use_container_width=True, hide_index=True)
la1, la2, la3 = st.columns(3)
la1.metric("Dead load allowance", f"{load_dead_total:.2f} kN/m²")
la2.metric("Live load allowance", f"{load_live:.2f} kN/m²")
la3.metric("Service area load", f"{load_service_area:.2f} kN/m²")
st.info(
    "Wind and earthquake actions are not calculated in this prototype because a defensible design needs verified "
    "site parameters, building height/geometry, exposure, seismic zone and the applicable current code workflow. "
    "Do not treat these assumed area loads as approved design loads."
)


# ---------- member selection and design estimates ----------
st.subheader("5. Structural design — select a member")
member_kind = st.radio("Member type", ["Beam", "Column", "Slab", "Foundation"], horizontal=True)
if member_kind == "Beam":
    member_ids = [b["id"] for b in beams]
elif member_kind == "Column":
    member_ids = [c["id"] for c in columns]
elif member_kind == "Slab":
    member_ids = [s["id"] for s in slabs]
else:
    member_ids = [f["id"] for f in footings]
selected_id = st.selectbox("Choose member ID", member_ids)

# Explicit demo assumptions for load and member sizing; do not represent as validated design.
concrete_density = 25.0 # kN/m3
live_load = 2.0 if building_type in ["Residential", "Mixed use"] else 3.0 # kN/m2, illustrative only
dead_slab_load = 0.15 * concrete_density
floor_height = 3.0
concrete_rate = 7500.0 # INR/m3 placeholder
steel_rate = 75.0 # INR/kg placeholder
steel_factor_beam = 110.0 # kg/m3 placeholder
steel_factor_column = 130.0
steel_factor_slab = 80.0
steel_factor_footing = 75.0

def draw_section(kind, width, depth, label):
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((0, 0), width, depth, fill=False, linewidth=2.5, edgecolor="#334155"))
    cover = min(0.04, width*0.12, depth*0.12)
    # diagrammatic bars/stirrups only; reinforcement must be designed/verified
    if kind in ["Beam", "Column"]:
        xs = np.linspace(cover+0.03, width-cover-0.03, 2 if width > .2 else 1)
        ys = [cover+0.03, depth-cover-0.03]
        for x in xs:
            for y in ys:
                ax.scatter(x, y, s=38, color="#dc2626", zorder=3)
        ax.add_patch(Rectangle((cover, cover), max(.01, width-2*cover), max(.01, depth-2*cover), fill=False, linestyle="--", linewidth=1.3, edgecolor="#64748b"))
    else:
        for x in np.linspace(cover+0.02, width-cover-0.02, 5):
            ax.scatter(x, depth/2, s=22, color="#dc2626")
    ax.annotate("", xy=(0, -depth*.15), xytext=(width, -depth*.15), arrowprops=dict(arrowstyle="<->"))
    ax.text(width/2, -depth*.24, f"{width*1000:.0f} mm", ha="center", va="top", fontsize=9)
    ax.annotate("", xy=(-width*.15, 0), xytext=(-width*.15, depth), arrowprops=dict(arrowstyle="<->"))
    ax.text(-width*.22, depth/2, f"{depth*1000:.0f} mm", rotation=90, ha="center", va="center", fontsize=9)
    ax.set_xlim(-width*.35, width*1.15); ax.set_ylim(-depth*.38, depth*1.15); ax.axis("off")
    ax.set_title(f"{label} — schematic cross-section")
    fig.tight_layout()
    return fig

if member_kind == "Beam":
    bm = next(b for b in beams if b["id"] == selected_id)
    span = max(bm["span"], 1.0)
    bw, bd = 0.25, max(0.30, span/12)
    tributary_width = max(min(approx_l / max(len(grid_y)-1, 1), 4.0), 1.0)
    line_load = (dead_slab_load + live_load) * tributary_width + bw*bd*concrete_density
    reaction = line_load*span/2
    vmax = reaction
    mmax = line_load*span**2/8
    E = 25e6 # kN/m2 illustrative
    I = bw*bd**3/12
    deflection_m = 5*line_load*span**4/(384*E*I)
    volume = bw*bd*span
    steel_kg = volume*steel_factor_beam
    fig_sec = draw_section("Beam", bw, bd, selected_id)
    # SFD/BMD plots are shown in Section 6 (Structural analysis), not here.
    result_rows = [
        ["Member", selected_id], ["Span", f"{span:.2f} m"], ["Trial section", f"{bw*1000:.0f} × {bd*1000:.0f} mm"],
        ["Illustrative line load", f"{line_load:.2f} kN/m"], ["Reaction at each support", f"{reaction:.2f} kN"],
        ["Maximum shear", f"{vmax:.2f} kN"], ["Maximum moment", f"{mmax:.2f} kN·m"],
        ["Estimated elastic deflection", f"{deflection_m*1000:.2f} mm"], ["Concrete volume", f"{volume:.3f} m³"],
        ["Steel quantity allowance", f"{steel_kg:.1f} kg"], ["Concrete + steel placeholder cost", f"₹{volume*concrete_rate+steel_kg*steel_rate:,.0f}"]
    ]
elif member_kind == "Column":
    c = next(c for c in columns if c["id"] == selected_id)
    cw = cd = 0.30
    tributary = max((approx_w/3)*(approx_l/2), 1.0)
    load_per_floor = (dead_slab_load + live_load)*tributary
    axial = load_per_floor*chosen_floors + cw*cd*floor_height*concrete_density*chosen_floors
    volume = cw*cd*floor_height*chosen_floors
    steel_kg = volume*steel_factor_column
    fig_sec = draw_section("Column", cw, cd, selected_id)
    result_rows = [
        ["Member", selected_id], ["Storeys represented", str(chosen_floors)], ["Trial section", "300 × 300 mm"],
        ["Tributary area (approx.)", f"{tributary:.2f} m²"], ["Illustrative axial load", f"{axial:.2f} kN"],
        ["Concrete volume (storey length total)", f"{volume:.3f} m³"], ["Steel quantity allowance", f"{steel_kg:.1f} kg"],
        ["Concrete + steel placeholder cost", f"₹{volume*concrete_rate+steel_kg*steel_rate:,.0f}"]
    ]
elif member_kind == "Slab":
    s = next(s for s in slabs if s["id"] == selected_id)
    sw = s["x2"]-s["x1"]; sl = s["y2"]-s["y1"]; th = 0.15
    area = sw*sl; volume = area*th; steel_kg = volume*steel_factor_slab
    slab_load = dead_slab_load+live_load
    m_per_m = slab_load*min(sw, sl)**2/8
    fig_sec = draw_section("Slab", sw, th, selected_id)
    result_rows = [
        ["Member", selected_id], ["Panel dimensions", f"{sw:.2f} × {sl:.2f} m"], ["Trial thickness", "150 mm"],
        ["Panel area", f"{area:.2f} m²"], ["Illustrative area load", f"{slab_load:.2f} kN/m²"],
        ["Simple-strip moment indicator", f"{m_per_m:.2f} kN·m/m"], ["Concrete volume", f"{volume:.3f} m³"],
        ["Steel quantity allowance", f"{steel_kg:.1f} kg"], ["Concrete + steel placeholder cost", f"₹{volume*concrete_rate+steel_kg*steel_rate:,.0f}"]
    ]
else:
    f = next(f for f in footings if f["id"] == selected_id)
    fw = fd = 1.5; ft = 0.45
    tributary = max((approx_w/3)*(approx_l/2), 1.0)
    axial = (dead_slab_load+live_load)*tributary*chosen_floors
    soil_pressure = axial/(fw*fd)
    volume = fw*fd*ft; steel_kg = volume*steel_factor_footing
    fig_sec = draw_section("Foundation", fw, ft, selected_id)
    result_rows = [
        ["Member", selected_id], ["Supported column", f["column"]], ["Trial footing plan size", "1500 × 1500 mm"],
        ["Trial thickness", "450 mm"], ["Illustrative axial load", f"{axial:.2f} kN"],
        ["Average soil pressure indicator", f"{soil_pressure:.2f} kN/m²"],
        ["Concrete volume", f"{volume:.3f} m³"], ["Steel quantity allowance", f"{steel_kg:.1f} kg"],
        ["Concrete + steel placeholder cost", f"₹{volume*concrete_rate+steel_kg*steel_rate:,.0f}"],
        ["Bearing check", "Cannot verify without site-specific allowable soil pressure"]
    ]

left, right = st.columns([1, 1.3])
with left:
    st.pyplot(fig_sec, use_container_width=True)
    plt.close(fig_sec)
with right:
    st.markdown(f"### {member_kind} {selected_id} — estimate")
    st.dataframe(pd.DataFrame(result_rows, columns=["Parameter", "Result"]), use_container_width=True, hide_index=True)
st.caption("Member sections and reinforcement markers are schematic. The app does not perform complete code-based RC design or prove load capacity. Steel values are quantity allowances, not reinforcement detailing.")


st.subheader("6. Structural analysis")
st.caption(
    "The beam example below calculates a simply supported member under a uniform line load, with its assumptions shown. "
    "It is a simplified demonstration—not a full 3D building analysis or proof of RCC capacity."
)
analysis_beam_id = st.selectbox("Choose a beam for analysis", [b["id"] for b in beams], key="analysis_beam_id")
analysis_beam = next(b for b in beams if b["id"] == analysis_beam_id)
analysis_span = max(float(analysis_beam["span"]), 1.0)
analysis_bw, analysis_bd = 0.25, max(0.30, analysis_span / 12.0)
analysis_trib_width = max(min(approx_l / max(len(grid_y)-1, 1), 4.0), 1.0)
analysis_self_weight = analysis_bw * analysis_bd * 25.0
analysis_line_load = load_service_area * analysis_trib_width + analysis_self_weight
analysis_reaction = analysis_line_load * analysis_span / 2.0
analysis_vmax = analysis_reaction
analysis_mmax = analysis_line_load * analysis_span**2 / 8.0
analysis_E = 25e6  # kN/m² illustrative elastic modulus
analysis_I = analysis_bw * analysis_bd**3 / 12.0
analysis_deflection = 5 * analysis_line_load * analysis_span**4 / (384 * analysis_E * analysis_I)
analysis_x = np.linspace(0, analysis_span, 120)
analysis_V = analysis_line_load * analysis_span / 2 - analysis_line_load * analysis_x
analysis_M = analysis_line_load * analysis_x * (analysis_span - analysis_x) / 2
sa1, sa2, sa3, sa4 = st.columns(4)
sa1.metric("Span", f"{analysis_span:.2f} m")
sa2.metric("Line load", f"{analysis_line_load:.2f} kN/m")
sa3.metric("Peak moment", f"{analysis_mmax:.2f} kN·m")
sa4.metric("Estimated deflection", f"{analysis_deflection*1000:.2f} mm")
plot1, plot2 = st.columns(2)
with plot1:
    af1, aax1 = plt.subplots(figsize=(6.2, 3.0))
    aax1.plot(analysis_x, analysis_V, color="#1d4ed8", lw=2)
    aax1.fill_between(analysis_x, analysis_V, 0, alpha=.16, color="#60a5fa")
    aax1.axhline(0, color="black", lw=.8)
    aax1.set_title(f"{analysis_beam_id} — Shear Force Diagram (SFD)")
    aax1.set_xlabel("Distance along span (m)")
    aax1.set_ylabel("Shear force (kN)")
    aax1.grid(alpha=.25)
    af1.tight_layout()
    st.pyplot(af1, use_container_width=True)
    plt.close(af1)
with plot2:
    af2, aax2 = plt.subplots(figsize=(6.2, 3.0))
    aax2.plot(analysis_x, analysis_M, color="#15803d", lw=2)
    aax2.fill_between(analysis_x, analysis_M, 0, alpha=.16, color="#86efac")
    aax2.axhline(0, color="black", lw=.8)
    aax2.set_title(f"{analysis_beam_id} — Bending Moment Diagram (BMD)")
    aax2.set_xlabel("Distance along span (m)")
    aax2.set_ylabel("Moment (kN·m)")
    aax2.grid(alpha=.25)
    af2.tight_layout()
    st.pyplot(af2, use_container_width=True)
    plt.close(af2)
analysis_results = pd.DataFrame([
    ["Support reaction (each end, symmetric)", f"{analysis_reaction:.2f} kN"],
    ["Maximum shear force", f"{analysis_vmax:.2f} kN"],
    ["Maximum bending moment", f"{analysis_mmax:.2f} kN·m"],
    ["Estimated elastic midspan deflection", f"{analysis_deflection*1000:.2f} mm"],
    ["Model", "Simply supported beam + uniform line load"],
    ["Load basis", f"{load_service_area:.2f} kN/m² × {analysis_trib_width:.2f} m tributary width + beam self-weight"],
], columns=["Analysis output", "Result"])
st.dataframe(analysis_results, use_container_width=True, hide_index=True)

st.markdown("### Element-wise analysis overview — beams, columns, slabs and foundations")
st.caption(
    "The following are preliminary screening indicators for each generated element category using simplified assumptions. "
    "They are not a coordinated frame analysis, and no pass/fail capacity claim is made without verified sections, reinforcement, material grades, load combinations and soil data."
)

# Columns: tributary-area axial-load indicator and slenderness indicator using assumed trial dimensions.
column_rows = []
column_b = 0.30  # m, illustrative trial section only
column_h = 0.30  # m, illustrative trial section only
column_height = 3.0 * chosen_floors
column_area = max(approx_w * approx_l / max(len(columns), 1), 1.0)
for col in columns:
    axial_indicator = (dead_slab_load + live_load) * column_area * chosen_floors
    column_rows.append({
        "Column": col["id"], "Trial section (mm)": "300 × 300 (assumed)",
        "Axial load indicator (kN)": round(axial_indicator, 2),
        "Storey-height assumption (m)": 3.0,
        "Slenderness indicator (height / smaller dimension)": round(3.0 / min(column_b, column_h), 2),
        "Status": "NOT APPROVED — frame analysis and IS 456 checks required"
    })
st.markdown("#### Columns — axial load and stability screening")
st.dataframe(pd.DataFrame(column_rows), use_container_width=True, hide_index=True)
st.caption("Column bending and shear demand require a frame analysis with beam-column stiffness, end conditions, lateral loads and load combinations; these are not solved by this screening table.")

# Slabs: simple one-way strip indicator. Actual slab action depends on panel aspect ratio, continuity and support conditions.
slab_rows = []
for slab in slabs:
    lx = max(abs(float(slab["x2"]) - float(slab["x1"])), 0.1)
    ly = max(abs(float(slab["y2"]) - float(slab["y1"])), 0.1)
    short_span = min(lx, ly)
    slab_load = load_service_area
    slab_moment = slab_load * short_span**2 / 8.0  # kN·m per m width, simply supported strip indicator
    slab_shear = slab_load * short_span / 2.0     # kN per m width
    slab_rows.append({
        "Slab": slab["id"], "Panel (m)": f"{lx:.2f} × {ly:.2f}",
        "Service area load (kN/m²)": round(slab_load, 2),
        "Short-span strip BM (kN·m/m)": round(slab_moment, 2),
        "Short-span strip SF (kN/m)": round(slab_shear, 2),
        "Status": "NOT APPROVED — slab reinforcement, continuity and deflection checks required"
    })
st.markdown("#### Slabs — short-span strip bending and shear indicators")
st.dataframe(pd.DataFrame(slab_rows), use_container_width=True, hide_index=True)
st.caption("Slab deflection, reinforcement, punching shear and two-way action are not checked by this simplified strip indicator.")

# Foundations: use a trial footing size and estimate average pressure from the column axial-load indicator.
foundation_rows = []
trial_footing_w = 1.5
trial_footing_l = 1.5
for footing in footings:
    axial_indicator = (dead_slab_load + live_load) * column_area * chosen_floors
    pressure_indicator = axial_indicator / (trial_footing_w * trial_footing_l)
    foundation_rows.append({
        "Foundation": footing["id"], "Supported column": footing["column"],
        "Trial footing (m)": "1.5 × 1.5 (assumed)",
        "Axial load indicator (kN)": round(axial_indicator, 2),
        "Average soil pressure indicator (kN/m²)": round(pressure_indicator, 2),
        "Status": "NOT APPROVED — geotechnical data and footing checks required"
    })
st.markdown("#### Foundations — axial load and soil-pressure indicators")
st.dataframe(pd.DataFrame(foundation_rows), use_container_width=True, hide_index=True)
st.caption("No bearing-capacity pass/fail result is possible because allowable soil pressure and groundwater/site conditions are not provided. Foundation flexure, one-way shear and punching shear are not verified.")

st.markdown("### Overall beam-wise SFD and BMD")
st.caption(
    "This overview checks every generated beam in the concept layout and compares each beam's peak shear force and bending moment. "
    "Curves are plotted against normalized span (0–100%) so beams of different lengths can be compared. "
    "It is not a summed whole-building analysis; a coordinated 3D structural model is required for that."
)
overall_rows = []
all_beam_curves = []
normalized_x = np.linspace(0, 1, 120)
for beam_item in beams:
    span_i = max(float(beam_item["span"]), 1.0)
    bw_i, bd_i = 0.25, max(0.30, span_i / 12.0)
    trib_i = max(min(approx_l / max(len(grid_y)-1, 1), 4.0), 1.0)
    self_weight_i = bw_i * bd_i * 25.0
    line_load_i = load_service_area * trib_i + self_weight_i
    x_i = normalized_x * span_i
    shear_i = line_load_i * span_i / 2 - line_load_i * x_i
    moment_i = line_load_i * x_i * (span_i - x_i) / 2
    max_shear_i = line_load_i * span_i / 2
    max_moment_i = line_load_i * span_i**2 / 8
    overall_rows.append({
        "Beam": beam_item["id"], "Span (m)": round(span_i, 2),
        "Line load (kN/m)": round(line_load_i, 2),
        "Maximum |SF| (kN)": round(max_shear_i, 2),
        "Maximum BM (kN·m)": round(max_moment_i, 2),
    })
    all_beam_curves.append((beam_item["id"], shear_i, moment_i))
overall_df = pd.DataFrame(overall_rows)
st.dataframe(overall_df, use_container_width=True, hide_index=True)
if all_beam_curves:
    overall_plot1, overall_plot2 = st.columns(2)
    with overall_plot1:
        of1, oax1 = plt.subplots(figsize=(6.2, 3.4))
        for beam_label, shear_curve, _ in all_beam_curves:
            oax1.plot(normalized_x * 100, shear_curve, lw=1.7, label=beam_label)
        oax1.axhline(0, color="black", lw=.8)
        oax1.set_title("Overall Beam-wise Shear Force Diagrams")
        oax1.set_xlabel("Normalized span (%)")
        oax1.set_ylabel("Shear force (kN)")
        oax1.grid(alpha=.25)
        oax1.legend(fontsize=7, ncol=2)
        of1.tight_layout()
        st.pyplot(of1, use_container_width=True)
        plt.close(of1)
    with overall_plot2:
        of2, oax2 = plt.subplots(figsize=(6.2, 3.4))
        for beam_label, _, moment_curve in all_beam_curves:
            oax2.plot(normalized_x * 100, moment_curve, lw=1.7, label=beam_label)
        oax2.axhline(0, color="black", lw=.8)
        oax2.set_title("Overall Beam-wise Bending Moment Diagrams")
        oax2.set_xlabel("Normalized span (%)")
        oax2.set_ylabel("Bending moment (kN·m)")
        oax2.grid(alpha=.25)
        oax2.legend(fontsize=7, ncol=2)
        of2.tight_layout()
        st.pyplot(of2, use_container_width=True)
        plt.close(of2)
    st.metric("Highest beam-wise shear force", f"{overall_df['Maximum |SF| (kN)'].max():.2f} kN")
    st.metric("Highest beam-wise bending moment", f"{overall_df['Maximum BM (kN·m)'].max():.2f} kN·m")
st.warning(
    "This analysis does not yet include a coordinated building-wide stiffness model, load combinations, "
    "lateral analysis, torsion, support settlement, or code-based strength/serviceability verification. "
    "Use it as a demonstration only; a qualified structural engineer must verify any real design."
)

# ---------- building quantities and cost ----------
st.subheader("7. Whole-building material and cost estimate")
st.caption("The table explicitly lists the materials being costed. Quantities are preliminary area-factor allowances, not a measured bill of quantities.")
# Transparent prototype quantities/rates. Concrete ingredients are split out for clarity.
concrete_vol = total_area * 0.22
cement_bags = concrete_vol * 8.0            # approximate illustrative conversion
sand_m3 = concrete_vol * 0.44               # approximate nominal-mix allowance
aggregate_m3 = concrete_vol * 0.88           # approximate nominal-mix allowance
steel_kg_total = total_area * 35.0
formwork_m2 = total_area * 1.2
masonry_m2 = total_area * 1.1
brick_units = masonry_m2 * 12.5              # approximate units/m² allowance
plaster_m2 = masonry_m2 * 2.0
flooring_m2 = total_area
material_rows = [
    {"Material / work item": "Cement (bags, 50 kg each)", "Quantity": round(cement_bags, 1), "Unit": "bag", "Rate (₹/unit)": 420.0},
    {"Material / work item": "Fine aggregate / sand", "Quantity": round(sand_m3, 2), "Unit": "m³", "Rate (₹/unit)": 1800.0},
    {"Material / work item": "Coarse aggregate", "Quantity": round(aggregate_m3, 2), "Unit": "m³", "Rate (₹/unit)": 1500.0},
    {"Material / work item": "Reinforcement steel (TMT bars)", "Quantity": round(steel_kg_total, 1), "Unit": "kg", "Rate (₹/unit)": steel_rate},
    {"Material / work item": "Formwork / shuttering", "Quantity": round(formwork_m2, 2), "Unit": "m²", "Rate (₹/unit)": 350.0},
    {"Material / work item": "Brick / block masonry (allowance)", "Quantity": round(brick_units, 0), "Unit": "units", "Rate (₹/unit)": 12.0},
    {"Material / work item": "Internal + external plastering", "Quantity": round(plaster_m2, 2), "Unit": "m²", "Rate (₹/unit)": 180.0},
    {"Material / work item": "Floor finish / tiles", "Quantity": round(flooring_m2, 2), "Unit": "m²", "Rate (₹/unit)": 650.0},
]
for row in material_rows:
    row["Amount (₹)"] = round(row["Quantity"] * row["Rate (₹/unit)"], 2)
materials_total = sum(r["Amount (₹)"] for r in material_rows)
materials_df = pd.DataFrame(material_rows)
st.dataframe(materials_df, use_container_width=True, hide_index=True)
labour = materials_total * 0.25
contingency = (materials_total + labour) * 0.05
grand_total = materials_total + labour + contingency
m1, m2, m3 = st.columns(3)
m1.metric("Listed materials / work items", f"₹{materials_total:,.0f}")
m2.metric("Labour allowance (25%)", f"₹{labour:,.0f}")
m3.metric("Indicative total incl. 5% contingency", f"₹{grand_total:,.0f}")
st.caption("Rates are editable illustrative placeholders, not live supplier quotations. Cement/sand/aggregate conversions use a rough concrete allowance; verify mix design, wastage, local rates, taxes, transport and measured drawings before procurement. The table does not yet include doors/windows, plumbing, electrical, paint, waterproofing, excavation, or a measured reinforcement bar-bending schedule.")

# ---------- report ----------
st.subheader("8. Final report")
report = f"""BUILDWISE AI — CONCEPT REPORT

Location: {location}
Building type: {building_type}
Plot area: {plot_area:.2f} m²
Assumed plot dimensions: {plot_width:.2f} m × {plot_length:.2f} m
Chosen option: {option_labels[chosen_floors]}
Concept footprint: {floor_plate:.2f} m²
Indicative total floor area: {total_area:.2f} m²
Preliminary service area load: {load_service_area:.2f} kN/m²
Analyzed beam: {analysis_beam_id}
Beam span: {analysis_span:.2f} m
Illustrative beam line load: {analysis_line_load:.2f} kN/m
Illustrative maximum beam moment: {analysis_mmax:.2f} kN·m

Verification status: PRELIMINARY SCREENING ONLY — NOT APPROVED
- No statutory approval is issued. Local planning rules, soil capacity, wind/seismic design and complete RCC code checks are not verified.

Code framework to verify during professional review:
- Planning: applicable current local/state building rules and amendments.
- RCC: IS 456; loads: relevant parts of IS 875; soil investigation/foundations: IS 1892 and IS 1904; earthquake design: applicable current IS 1893 provisions.
- Listing a code is not evidence that the design complies with it.

Important limitations:
- Plot shape, coverage and setbacks are assumptions, not verified site data.
- Local planning permission, FAR/FSI, height and fire requirements are not verified.
- Soil capacity is unknown without geotechnical information.
- Architectural plans are dimensioned concept drafts, not permit-ready drawings. Beam and footing detail sketches are schematic.
- Member values and steel quantities are illustrative and are not proof of capacity or code compliance.
- Structural design and all calculations must be independently validated before construction.

Indicative materials/work items: ₹{materials_total:,.0f}\nLabour allowance: ₹{labour:,.0f}\nContingency: ₹{contingency:,.0f}\nIndicative total cost: ₹{grand_total:,.0f}
"""
st.download_button("⬇️ Download concept report (TXT)", data=report, file_name="buildwise_concept_report.txt", mime="text/plain")
st.success("Workflow displayed: inputs → candidate floor options → architectural plans → RCC layout → load analysis → element-wise structural analysis indicators → member estimates → material estimate → report.")
