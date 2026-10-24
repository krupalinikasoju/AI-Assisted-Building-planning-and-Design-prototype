# BuildWise AI — Building Planning & Preliminary RCC Workflow

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`
4. Run `streamlit run app.py`
5. Open the local URL Streamlit prints.

## Deploy on Streamlit Community Cloud
Upload `app.py`, `requirements.txt`, and this README to the root of a GitHub repository. Connect that repository in Streamlit Community Cloud and set the main file path to `app.py`.

## Current prototype features
- Exactly three project inputs: location, plot area, and building type.
- Candidate floor options for user selection.
- Per-floor draft-style concept plans with overall dimensions, room labels and estimated room dimensions, door-swing symbols and window markers.
- RCC grid with column, beam and slab labels.
- Always-visible beam longitudinal elevation and cross-section, plus footing plan and section diagrams.
- Member selector for beam, column, slab and foundation with preliminary quantity/cost information; beam example includes illustrative SFD/BMD.
- Itemized preliminary materials/work estimate: cement, sand, coarse aggregate, TMT steel, formwork, masonry units, plastering and flooring.
- PNG downloads for drawings and a downloadable concept report.

## Important limitations
This is an educational concept prototype, not construction-ready design software. Plot shape, room arrangement, setbacks, coverage, loads, member sizes, reinforcement markers, quantities and unit rates use assumptions. The floor plan is not a permit-ready architectural drawing; the beam and footing details are schematic and do not constitute reinforcement detailing. The app does not perform a complete building-wide structural solver or establish code compliance, soil bearing capacity, reinforcement adequacy, or local planning permission. The material estimate is an allowance rather than a measured BOQ and excludes several trades. Obtain site survey and geotechnical data and have the design independently checked by qualified local professionals before construction or permitting.
