import streamlit as st
import math
import csv
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="TradeEstimator", layout="centered")

# -------------------------
# MOBILE / UI STYLING
# -------------------------

st.markdown(
    """
    <style>
    .main {
        max-width: 850px;
    }
    .stButton>button {
        width: 100%;
        height: 48px;
        font-size: 18px;
        font-weight: bold;
    }
    .stDownloadButton>button {
        width: 100%;
        height: 48px;
        font-size: 17px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# BRANDING
# -------------------------

st.title("TradeEstimator")
st.markdown("### Fast Drywall, Framing & Quote Tool")
st.write("Built for quick material counts, labour pricing, and contractor-ready estimates.")

st.divider()

# -------------------------
# SIDEBAR SETTINGS
# -------------------------

st.sidebar.header("Quick Pricing Mode")

preset = st.sidebar.selectbox(
    "Pricing Preset",
    ["Custom", "Cheap Job", "Standard Job", "Premium Job"]
)

if preset == "Cheap Job":
    default_lf = 8.0
    default_stud = 6.0
    default_profit = 10
elif preset == "Standard Job":
    default_lf = 11.0
    default_stud = 8.0
    default_profit = 20
elif preset == "Premium Job":
    default_lf = 14.0
    default_stud = 10.0
    default_profit = 30
else:
    default_lf = 11.0
    default_stud = 8.0
    default_profit = 20

st.sidebar.header("Labour Pricing")

price_per_lf = st.sidebar.number_input("Labour $ / Linear Foot", min_value=0.0, value=default_lf, step=0.5)
price_per_stud = st.sidebar.number_input("Labour $ / Stud", min_value=0.0, value=default_stud, step=0.5)
door_price = st.sidebar.number_input("Door Add-On $", min_value=0.0, value=60.0, step=5.0)

pricing_method = st.sidebar.selectbox(
    "Pricing Method",
    ["Per Linear Foot", "Per Stud"]
)

profit_margin = st.sidebar.slider("Profit Margin %", 0, 100, default_profit)

st.sidebar.divider()

st.sidebar.header("Material Costs")

stud_cost = st.sidebar.number_input("Cost per Metal Stud $", min_value=0.0, value=7.50, step=0.25)
track_cost = st.sidebar.number_input("Cost per Track Piece $", min_value=0.0, value=8.50, step=0.25)
drywall_cost = st.sidebar.number_input("Cost per Drywall Sheet $", min_value=0.0, value=18.00, step=0.5)
drywall_screw_box_cost = st.sidebar.number_input("Drywall Screw Allowance $", min_value=0.0, value=25.00, step=1.0)
framing_screw_box_cost = st.sidebar.number_input("Framing Screw Allowance $", min_value=0.0, value=20.00, step=1.0)
channel_cost = st.sidebar.number_input("Cost per Channel Piece $", min_value=0.0, value=9.00, step=0.25)

material_markup = st.sidebar.slider("Material Markup %", 0, 100, 15)

st.sidebar.divider()

st.sidebar.header("Material Settings")

stud_spacing = st.sidebar.selectbox("Stud Spacing", ["16 inches", "24 inches"])
board_both_sides = st.sidebar.checkbox("Board Both Sides", value=True)
include_waste = st.sidebar.checkbox("Include 10% Waste", value=True)

# -------------------------
# PROJECT DETAILS
# -------------------------

st.subheader("Project Details")

project_name = st.text_input("Project Name", value="Test Project")
client_name = st.text_input("Client Name", value="Client")

col1, col2 = st.columns(2)

with col1:
    wall_height = st.selectbox("Wall Height (ft)", [8, 9, 10, 12], index=1)

with col2:
    doors = st.number_input("Door Openings", min_value=0, value=1)

system_type = st.selectbox(
    "Wall System",
    [
        "Direct to Metal Studs",
        "One Row Furring Channel",
        "Full Furring Channel Rows",
        "Resilient Channel"
    ]
)

st.divider()

# -------------------------
# MULTI-WALL INPUT
# -------------------------

st.subheader("Walls")

num_walls = st.number_input("Number of Walls", min_value=1, value=1)

wall_lengths = []

for i in range(int(num_walls)):
    length = st.number_input(
        f"Wall {i + 1} Length (ft)",
        min_value=1.0,
        value=36.0 if i == 0 else 10.0,
        step=0.5,
        key=f"wall_{i}"
    )
    wall_lengths.append(length)

total_wall_length = sum(wall_lengths)

st.info(f"Total wall length: {total_wall_length} ft")

st.divider()

# -------------------------
# CALCULATIONS
# -------------------------

spacing_ft = 16 / 12 if stud_spacing == "16 inches" else 24 / 12

regular_studs = math.ceil(total_wall_length / spacing_ft)
end_studs = int(num_walls) * 2

door_king_studs = doors * 2
door_jack_studs = doors * 2

total_studs = regular_studs + end_studs + door_king_studs + door_jack_studs

track_linear_ft = total_wall_length * 2
track_pieces = math.ceil(track_linear_ft / 10)

wall_area_one_side = total_wall_length * wall_height
drywall_area = wall_area_one_side * 2 if board_both_sides else wall_area_one_side

base_drywall_sheets = math.ceil(drywall_area / 32)

drywall_sheets = math.ceil(base_drywall_sheets * 1.10) if include_waste else base_drywall_sheets

drywall_screws = drywall_sheets * 35
framing_screws = total_studs * 4 + doors * 20

channel_linear_ft = 0
channel_pieces = 0

if system_type == "Direct to Metal Studs":
    channel_note = "No carrying/furring channel needed for direct drywall-to-stud install."

elif system_type == "One Row Furring Channel":
    channel_linear_ft = total_wall_length
    channel_pieces = math.ceil(channel_linear_ft / 12)
    channel_note = "One row is usually for backing/blocking, not full drywall support."

elif system_type == "Full Furring Channel Rows":
    rows = math.ceil(wall_height / 2)
    channel_linear_ft = rows * total_wall_length
    channel_pieces = math.ceil(channel_linear_ft / 12)
    channel_note = f"Estimated {rows} rows of furring channel."

else:
    rows = math.ceil(wall_height / 2)
    channel_linear_ft = rows * total_wall_length
    channel_pieces = math.ceil(channel_linear_ft / 12)
    channel_note = f"Estimated {rows} rows of resilient channel. Confirm spacing/spec."

# Labour pricing
if pricing_method == "Per Linear Foot":
    base_labour = total_wall_length * price_per_lf
else:
    base_labour = total_studs * price_per_stud

door_add_on = doors * door_price
labour_subtotal = base_labour + door_add_on

# Material pricing
material_subtotal = (
    total_studs * stud_cost
    + track_pieces * track_cost
    + drywall_sheets * drywall_cost
    + drywall_screw_box_cost
    + framing_screw_box_cost
    + channel_pieces * channel_cost
)

material_markup_amount = material_subtotal * (material_markup / 100)
material_total = material_subtotal + material_markup_amount

subtotal = labour_subtotal + material_total
profit_amount = subtotal * (profit_margin / 100)
suggested_price = subtotal + profit_amount

# -------------------------
# OUTPUT
# -------------------------

st.subheader("Estimate Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Metal Studs", f"{total_studs} pcs")
    st.metric("Track", f"{track_pieces} pcs")
    st.metric("Drywall", f"{drywall_sheets} sheets")

with col2:
    st.metric("Drywall Screws", f"{drywall_screws}")
    st.metric("Framing Screws", f"{framing_screws}")
    st.metric("Channel", f"{channel_pieces} pcs")

st.divider()

st.subheader("Layout Logic")

st.write(f"Total wall length: **{total_wall_length} ft**")
st.write(f"Wall height: **{wall_height} ft**")
st.write(f"Stud spacing: **{stud_spacing}**")
st.write(f"Door openings: **{doors}**")
st.write(f"Wall system: **{system_type}**")

if wall_height == 9:
    st.warning("9 ft wall: expect extra seams or rip strips if using 4x8 drywall.")
elif wall_height > 9:
    st.warning("Tall wall: confirm board size/layout to reduce seams.")
else:
    st.success("Standard wall height.")

if system_type == "Direct to Metal Studs":
    st.success(channel_note)
elif system_type == "One Row Furring Channel":
    st.warning(channel_note)
else:
    st.info(channel_note)

st.divider()

st.subheader("Pricing")

col3, col4 = st.columns(2)

with col3:
    st.metric("Labour Subtotal", f"${labour_subtotal:.2f}")
    st.metric("Material Total", f"${material_total:.2f}")
    st.metric("Subtotal", f"${subtotal:.2f}")

with col4:
    st.metric("Material Markup", f"${material_markup_amount:.2f}")
    st.metric("Profit Added", f"${profit_amount:.2f}")
    st.metric("Suggested Price", f"${suggested_price:.2f}")

st.divider()

# -------------------------
# QUOTE TEXT
# -------------------------

quote = f"""
TRADEESTIMATOR QUOTE

Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Project: {project_name}
Client: {client_name}

WALL DETAILS
Total Wall Length: {total_wall_length} ft
Wall Height: {wall_height} ft
Number of Walls: {num_walls}
Door Openings: {doors}
Stud Spacing: {stud_spacing}
Wall System: {system_type}
Board Both Sides: {board_both_sides}
Waste Factor Included: {include_waste}

MATERIALS
Metal Studs: {total_studs} pcs
Track: {track_pieces} pcs
Drywall: {drywall_sheets} sheets
Drywall Screws: {drywall_screws}
Framing Screws: {framing_screws}
Channel: {channel_pieces} pcs
Channel Linear Feet: {channel_linear_ft} ft

PRICING
Pricing Method: {pricing_method}
Base Labour: ${base_labour:.2f}
Door Add-On: ${door_add_on:.2f}
Labour Subtotal: ${labour_subtotal:.2f}

Material Subtotal: ${material_subtotal:.2f}
Material Markup: {material_markup}%
Material Total: ${material_total:.2f}

Subtotal: ${subtotal:.2f}
Profit Margin: {profit_margin}%
Profit Added: ${profit_amount:.2f}

SUGGESTED PRICE: ${suggested_price:.2f}

NOTES
{channel_note}
"""

safe_project_name = project_name.replace(" ", "_")

# -------------------------
# PDF GENERATOR
# -------------------------

def generate_pdf(file_name, text):
    c = canvas.Canvas(file_name, pagesize=letter)
    width, height = letter

    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "TradeEstimator Quote")
    y -= 30

    c.setFont("Helvetica", 10)

    for line in text.split("\n"):
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40

        c.drawString(40, y, line)
        y -= 14

    c.save()

pdf_file = f"{safe_project_name}_quote.pdf"
generate_pdf(pdf_file, quote)

st.subheader("Download Quote")

with open(pdf_file, "rb") as file:
    st.download_button(
        "Download PDF Quote",
        file,
        file_name=pdf_file
    )

st.download_button(
    "Download Text Quote",
    quote,
    file_name=f"{safe_project_name}_quote.txt"
)

st.divider()

# -------------------------
# SAVE JOB HISTORY
# -------------------------

st.subheader("Save Job")

if st.button("Save Job to History"):

    file_exists = os.path.exists("job_history.csv")

    with open("job_history.csv", "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Date",
                "Project",
                "Client",
                "Wall Length",
                "Height",
                "Studs",
                "Track",
                "Drywall",
                "Labour",
                "Materials",
                "Suggested Price"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            project_name,
            client_name,
            total_wall_length,
            wall_height,
            total_studs,
            track_pieces,
            drywall_sheets,
            labour_subtotal,
            material_total,
            suggested_price
        ])

    st.success("Job saved to history.")

if os.path.exists("job_history.csv"):
    st.subheader("Job History")

    df = pd.read_csv("job_history.csv")
    st.dataframe(df)

    with open("job_history.csv", "r") as file:
        st.download_button(
            "Download Job History",
            file,
            file_name="job_history.csv"
        )