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
rules_df = pd.DataFrame([
    ["Plot geometry", f"{plot_width:.2f} m × {plot_length:.2f} m", "Assumed from area; survey required"],
    ["Coverage used in concept", f"{coverage_assumption*100:.0f}%", "Placeholder only; verify local rules"],
    ["Setback used in concept", f"{setback_assumption:.1f} m each side", "Placeholder only; verify local rules"],
    ["Soil bearing capacity", "Not provided", "Geotechnical report required"],
    ["FAR/FSI / height / fire limits", "Not verified", "Check applicable local authority rules"],
], columns=["Assessment item", "Prototype value", "Status"])
st.dataframe(rules_df, use_container_width=True, hide_index=True)

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
    """Draw a CAD-style dimensioned concept floor plan with wall thickness, openings, fixtures and furniture.

    Geometry is generated from the estimated footprint; it is a concept drawing, not a
    permit-ready or construction drawing. Exact CAD/DWG deliverables require surveyed dimensions.
    """
    from matplotlib.patches import Rectangle, Arc, Circle

    # Use a consistent 3-column / 2-row plan grid with a central circulation strip.
    # Coordinates are derived from the footprint, so all partitions and dimensions agree.
    w = max(float(width), 5.0)
    L = max(float(length), 5.0)
    wall = min(0.18, w * 0.018, L * 0.018)  # illustrative exterior wall thickness
    part = min(0.12, w * 0.012, L * 0.012)  # illustrative internal partition thickness
    x1, x2 = w * 0.38, w * 0.70
    y1 = L * 0.48

    fig, ax = plt.subplots(figsize=(9, 9))
    fig.patch.set_facecolor("white")
    ax.set_aspect("equal")
    ax.set_xlim(-2.0, w + 1.6)
    ax.set_ylim(-2.0, L + 2.2)
    ax.axis("off")

    ink = "#111827"
    thin = "#374151"
    dimc = "#374151"
    furniture = "#64748b"
    windowc = "#0284c7"
    doorc = "#7c3aed"

    # CAD-style double-line external walls.
    ax.add_patch(Rectangle((0, 0), w, L, fill=False, edgecolor=ink, linewidth=2.2))
    ax.add_patch(Rectangle((wall, wall), w - 2*wall, L - 2*wall,
                           fill=False, edgecolor=ink, linewidth=0.9))

    # Internal partitions. Small white gaps represent door openings; opening symbols added below.
    # Horizontal partition split into three segments, leaving circulation/door gaps.
    for xa, xb in [(wall, x1-w*.055), (x1+w*.055, x2-w*.055), (x2+w*.055, w-wall)]:
        ax.plot([xa, xb], [y1, y1], color=ink, lw=1.5)
        ax.plot([xa, xb], [y1+part, y1+part], color=thin, lw=0.55)
    # Upper partitions, interrupted near room entries.
    for x, gap_y in [(x1, L*.72), (x2, L*.72)]:
        ax.plot([x, x], [y1+part, gap_y-.32], color=ink, lw=1.5)
        ax.plot([x+part, x+part], [y1+part, gap_y-.32], color=thin, lw=0.55)
        ax.plot([x, x], [gap_y+.32, L-wall], color=ink, lw=1.5)
        ax.plot([x+part, x+part], [gap_y+.32, L-wall], color=thin, lw=0.55)
    # Lower partitions, with door gaps.
    for x, gap_y in [(x1, L*.23), (x2, L*.23)]:
        ax.plot([x, x], [wall, gap_y-.32], color=ink, lw=1.5)
        ax.plot([x+part, x+part], [wall, gap_y-.32], color=thin, lw=0.55)
        ax.plot([x, x], [gap_y+.32, y1], color=ink, lw=1.5)
        ax.plot([x+part, x+part], [gap_y+.32, y1], color=thin, lw=0.55)

    # Helpers: room labels, furniture and opening symbols.
    def room_label(xa, xb, ya, yb, name):
        ax.text((xa+xb)/2, (ya+yb)/2, name, ha="center", va="center", fontsize=8.2,
                color=ink, fontweight="bold", linespacing=1.35)

    def bed(cx, cy, bw, bh):
        ax.add_patch(Rectangle((cx-bw/2, cy-bh/2), bw, bh, fill=False, edgecolor=furniture, lw=.8))
        ax.plot([cx-bw/2, cx+bw/2], [cy+bh*.20, cy+bh*.20], color=furniture, lw=.6)
        ax.add_patch(Rectangle((cx-bw*.36, cy+bh*.22), bw*.30, bh*.18, fill=False, ec=furniture, lw=.55))
        ax.add_patch(Rectangle((cx+bw*.06, cy+bh*.22), bw*.30, bh*.18, fill=False, ec=furniture, lw=.55))

    def sofa(cx, cy, sw, sh):
        ax.add_patch(Rectangle((cx-sw/2, cy-sh/2), sw, sh, fill=False, ec=furniture, lw=.8))
        ax.plot([cx-sw/2, cx+sw/2], [cy, cy], color=furniture, lw=.6)
        for sx in [cx-sw/2+sw*.33, cx+sw/2-sw*.33]:
            ax.plot([sx, sx], [cy-sh/2, cy+sh/2], color=furniture, lw=.45)

    def door_on_vertical(x, y, door_width=.72, opens_right=True):
        # leaf and quarter-circle swing, conventionally shown in plan.
        direction = 1 if opens_right else -1
        ax.plot([x, x+direction*door_width], [y, y], color=doorc, lw=.8)
        theta1, theta2 = (0, 90) if opens_right else (90, 180)
        ax.add_patch(Arc((x, y), 2*door_width, 2*door_width, theta1=theta1, theta2=theta2,
                         color=doorc, lw=.65))

    def window_on_horizontal(xa, xb, y):
        ax.plot([xa, xb], [y, y], color="white", lw=4.0, solid_capstyle="butt", zorder=5)
        ax.plot([xa, xb], [y-wall*.25, y-wall*.25], color=windowc, lw=1.0, zorder=6)
        ax.plot([xa, xb], [y+wall*.25, y+wall*.25], color=windowc, lw=1.0, zorder=6)

    def window_on_vertical(x, ya, yb):
        ax.plot([x, x], [ya, yb], color="white", lw=4.0, solid_capstyle="butt", zorder=5)
        ax.plot([x-wall*.25, x-wall*.25], [ya, yb], color=windowc, lw=1.0, zorder=6)
        ax.plot([x+wall*.25, x+wall*.25], [ya, yb], color=windowc, lw=1.0, zorder=6)

    # Zone labels and simple fixture/furniture symbols. All room dimensions come from zone coordinates.
    if floor_idx == 0:
        names_top = ["BEDROOM 1", "KITCHEN", "BATH / WC"]
        names_bottom = ["LIVING", "DINING", "STAIR / UTILITY"]
    else:
        names_top = ["BEDROOM 2", "BEDROOM 3", "BATH / WC"]
        names_bottom = ["FAMILY LOUNGE", "MASTER BEDROOM", "STAIR / BALCONY"]
    xs = [wall, x1, x2, w-wall]
    # Top band uses a consistent label row; lower band follows the same vertical partition positions.
    for j, name in enumerate(names_top):
        room_label(xs[j], xs[j+1], y1+part, L-wall, f"{name}\n{xs[j+1]-xs[j]:.2f} × {L-wall-y1-part:.2f} m")
    for j, name in enumerate(names_bottom):
        room_label(xs[j], xs[j+1], wall, y1, f"{name}\n{xs[j+1]-xs[j]:.2f} × {y1-wall:.2f} m")

    # Furniture symbols are intentionally schematic, scaled to fit each zone.
    bed((wall+x1)/2, (y1+L-wall)/2, min((x1-wall)*.52, 1.65), min((L-wall-y1)*.48, 1.95))
    # Kitchen counter + sink/cooktop symbols
    ax.add_patch(Rectangle((x1+w*.035, L-wall-.42), max(.35, x2-x1-w*.07), .25, fill=False, ec=furniture, lw=.75))
    ax.add_patch(Rectangle((x1+w*.05, L-wall-.38), .20, .15, fill=False, ec=furniture, lw=.55))
    # Bath/WC symbols
    bx = (x2+w-wall)/2; by = (y1+L-wall)/2
    ax.add_patch(Rectangle((bx-.18, by+.25), .36, .28, fill=False, ec=furniture, lw=.65))
    ax.add_patch(Circle((bx, by-.12), radius=.13, fill=False, ec=furniture, lw=.65))
    sofa((wall+x1)/2, (wall+y1)/2, min((x1-wall)*.65, 1.8), .52)
    # Dining table
    ax.add_patch(Rectangle((x1+w*.04, L*.12), max(.45, (x2-x1)*.62), .65, fill=False, ec=furniture, lw=.75))
    for cx in [x1+w*.08, x1+w*.04+(x2-x1)*.55]:
        for cy in [L*.12-.10, L*.12+.75]:
            ax.add_patch(Rectangle((cx-.09, cy-.08), .18, .16, fill=False, ec=furniture, lw=.55))
    # Stair run in the right-bottom room: treads and direction arrow.
    sx0, sx1 = x2+w*.04, w-wall-w*.04
    sy0, sy1 = wall+L*.05, y1-L*.05
    if sx1 > sx0 and sy1 > sy0:
        ax.add_patch(Rectangle((sx0, sy0), sx1-sx0, sy1-sy0, fill=False, ec=furniture, lw=.75))
        for k in range(1, 7):
            yy = sy0 + (sy1-sy0)*k/7
            ax.plot([sx0, sx1], [yy, yy], color=furniture, lw=.45)
        ax.annotate("UP", xy=((sx0+sx1)/2, sy1-.1), xytext=((sx0+sx1)/2, sy0+.1),
                    arrowprops=dict(arrowstyle="->", lw=.7, color=furniture), ha="center", va="center", fontsize=6.5, color=furniture)

    # Main entrance opening on bottom exterior wall with swing arc.
    entry_x = w*.18
    entry_w = min(.95, w*.12)
    ax.plot([entry_x-entry_w/2, entry_x+entry_w/2], [0, 0], color="white", lw=4.5, zorder=7)
    ax.plot([entry_x-entry_w/2, entry_x-entry_w/2], [0, entry_w], color=doorc, lw=.85, zorder=8)
    ax.add_patch(Arc((entry_x-entry_w/2, 0), 2*entry_w, 2*entry_w, theta1=0, theta2=90, color=doorc, lw=.7, zorder=8))
    # Interior door leaves and arcs, plus windows in exterior walls.
    for x, y in [(x1, y1-.70), (x2, y1-.70), (x1, y1+.70), (x2, y1+.70)]:
        door_on_vertical(x, y, min(.62, L*.055), opens_right=(x == x1))
    for yy in [L*.22, L*.73]:
        window_on_vertical(0, yy-.42, yy+.42)
        window_on_vertical(w, yy-.42, yy+.42)
    window_on_horizontal(w*.28, w*.43, L)
    window_on_horizontal(w*.45, w*.58, 0)

    # Overall and chained dimensions, extension lines and dimension ticks.
    def hdim(xa, xb, y, label, base_y):
        ax.plot([xa, xa], [base_y, y], color=dimc, lw=.45)
        ax.plot([xb, xb], [base_y, y], color=dimc, lw=.45)
        ax.annotate("", xy=(xa, y), xytext=(xb, y), arrowprops=dict(arrowstyle="<->", lw=.65, color=dimc))
        ax.text((xa+xb)/2, y+.10, label, ha="center", va="bottom", fontsize=7.2, color=dimc)
    def vdim(ya, yb, x, label, base_x):
        ax.plot([base_x, x], [ya, ya], color=dimc, lw=.45)
        ax.plot([base_x, x], [yb, yb], color=dimc, lw=.45)
        ax.annotate("", xy=(x, ya), xytext=(x, yb), arrowprops=dict(arrowstyle="<->", lw=.65, color=dimc))
        ax.text(x-.10, (ya+yb)/2, label, rotation=90, ha="right", va="center", fontsize=7.2, color=dimc)
    hdim(0, w, L+1.15, f"{w:.2f} m", L)
    hdim(0, x1, L+.55, f"{x1:.2f}", L)
    hdim(x1, x2, L+.55, f"{x2-x1:.2f}", L)
    hdim(x2, w, L+.55, f"{w-x2:.2f}", L)
    vdim(0, L, -1.15, f"{L:.2f} m", 0)
    vdim(0, y1, -.55, f"{y1:.2f}", 0)
    vdim(y1, L, -.55, f"{L-y1:.2f}", 0)

    # North arrow, scale bar and drawing title block.
    ax.annotate("N", xy=(w+.85, L-.25), xytext=(w+.85, L-1.0),
                arrowprops=dict(arrowstyle="-|>", lw=1.0, color=ink), ha="center", fontsize=9, fontweight="bold")
    bar_y = -1.15
    bar_len = min(2.0, w*.35)
    ax.plot([0, bar_len], [bar_y, bar_y], color=ink, lw=2)
    ax.plot([0, 0], [bar_y-.07, bar_y+.07], color=ink, lw=.8)
    ax.plot([bar_len, bar_len], [bar_y-.07, bar_y+.07], color=ink, lw=.8)
    ax.text(bar_len/2, bar_y-.12, f"Scale bar: {bar_len:.1f} m", ha="center", va="top", fontsize=6.8, color=thin)
    ax.text(w, -1.55, f"BUILDWISE AI  |  {'GROUND FLOOR' if floor_idx == 0 else f'FLOOR {floor_idx+1}'}  |  CONCEPT PLAN",
            ha="right", va="center", fontsize=7.5, color=ink, fontweight="bold")
    ax.set_title("ARCHITECTURAL FLOOR PLAN — DIMENSIONED CAD-STYLE CONCEPT", fontsize=11, pad=16, color=ink, fontweight="bold")
    fig.tight_layout()
    return fig
st.subheader("2. Architectural plans — every selected floor")
st.caption("CAD-style concept plans show double-line wall thickness, room zoning, door swings, windows, basic furniture/fixtures, stair treads, chained dimensions and a north arrow. These are still concept drawings: surveyed plot geometry, exact room requirements, opening schedules, services, ventilation/daylight and local rules need architectural coordination.")
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
        plt.close(fig)

# ---------- coordinated concept structural grid ----------
grid_x = [0, approx_w/3, 2*approx_w/3, approx_w]
grid_y = [0, approx_l/2, approx_l]
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

st.subheader("5. Structural analysis")
st.caption(
    "The beam example below calculates a simply supported member under a uniform line load, with its assumptions shown. "
    "It is a simplified demonstration—not a full 3D building analysis or proof of RCC capacity."
)
analysis_beam_id = st.selectbox("Choose a beam for analysis", [b["id"] for b in beams], key="analysis_beam_id")
analysis_beam = next(b for b in beams if b["id"] == analysis_beam_id)
analysis_span = max(float(analysis_beam["span"]), 1.0)
analysis_bw, analysis_bd = 0.25, max(0.30, analysis_span / 12.0)
analysis_trib_width = max(approx_l / 4.0, 2.0)
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
st.warning(
    "This analysis does not yet include a coordinated building-wide stiffness model, load combinations, "
    "lateral analysis, torsion, support settlement, or code-based strength/serviceability verification. "
    "Use it as a demonstration only; a qualified structural engineer must verify any real design."
)

# ---------- member selection and design estimates ----------
st.subheader("6. Select any member for its diagram and estimate")
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
    tributary_width = max(approx_l/4, 2.0)
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
    fig1, ax1 = plt.subplots(figsize=(7, 2.5))
    x = np.linspace(0, span, 100)
    V = line_load*span/2 - line_load*x
    ax1.plot(x, V, color="#2563eb"); ax1.fill_between(x, V, 0, alpha=.15, color="#60a5fa")
    ax1.axhline(0, color="black", lw=.8); ax1.set_title(f"{selected_id} — Shear Force Diagram"); ax1.set_xlabel("Span (m)"); ax1.set_ylabel("Shear (kN)"); ax1.grid(alpha=.2); fig1.tight_layout()
    fig2, ax2 = plt.subplots(figsize=(7, 2.5))
    M = line_load*x*(span-x)/2
    ax2.plot(x, M, color="#059669"); ax2.fill_between(x, M, 0, alpha=.15, color="#34d399")
    ax2.axhline(0, color="black", lw=.8); ax2.set_title(f"{selected_id} — Bending Moment Diagram"); ax2.set_xlabel("Span (m)"); ax2.set_ylabel("Moment (kN·m)"); ax2.grid(alpha=.2); fig2.tight_layout()
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
if member_kind == "Beam":
    st.pyplot(fig1, use_container_width=True); st.pyplot(fig2, use_container_width=True)
    plt.close(fig1); plt.close(fig2)
st.caption("Member sections and reinforcement markers are schematic. The app does not perform complete code-based RC design or prove load capacity. Steel values are quantity allowances, not reinforcement detailing.")

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

Verification status: NOT A CONSTRUCTION DESIGN
- Local planning rules, soil capacity, wind/seismic design and complete RCC code checks are not verified.

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
st.success("Workflow displayed: inputs → candidate floor options → concept floor plans → load ledger → beam analysis with SFD/BMD → member estimates → material estimate → report.")
