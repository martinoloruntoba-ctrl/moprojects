import streamlit as st
import math
import csv
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="TradeEstimator", layout="centered")

st.title("TradeEstimator")
st.markdown("### Fast Commercial Wall + Ceiling Estimator")
st.write("Built for framing, drywall, channels, doors, layers, and quote generation.")

st.divider()

# -------------------------
# HELPERS
# -------------------------

def feet_inches_to_decimal(feet, inches):
    return feet + inches / 12

def decimal_to_feet_inches(value):
    feet = int(value)
    inches = round((value - feet) * 12)
    if inches == 12:
        feet += 1
        inches = 0
    return feet, inches

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

# -------------------------
# SCOPE
# -------------------------

scope = st.selectbox(
    "Scope of Work",
    [
        "Framing Only",
        "Drywall Only",
        "Framing + Drywall",
        "Ceiling Only",
        "Full Build"
    ]
)

needs_framing = scope in ["Framing Only", "Framing + Drywall", "Full Build"]
needs_drywall = scope in ["Drywall Only", "Framing + Drywall", "Full Build"]
needs_ceiling = scope in ["Ceiling Only", "Full Build"]

# -------------------------
# SIDEBAR PRICING
# -------------------------

st.sidebar.header("Pricing")

price_per_lf = st.sidebar.number_input("Labour $ / Linear Foot", min_value=0.0, value=11.0, step=0.5)
price_per_stud = st.sidebar.number_input("Labour $ / Stud", min_value=0.0, value=8.0, step=0.5)
door_price = st.sidebar.number_input("Door Add-On $", min_value=0.0, value=60.0, step=5.0)

pricing_method = st.sidebar.selectbox("Pricing Method", ["Per Linear Foot", "Per Stud"])
profit_margin = st.sidebar.slider("Profit Margin %", 0, 100, 20)

st.sidebar.divider()
st.sidebar.header("Material Costs")

stud_cost = st.sidebar.number_input("Cost per Stud $", min_value=0.0, value=7.50, step=0.25)
track_cost = st.sidebar.number_input("Cost per Track Piece $", min_value=0.0, value=8.50, step=0.25)
drywall_cost = st.sidebar.number_input("Cost per Drywall Sheet $", min_value=0.0, value=18.00, step=0.50)
channel_cost = st.sidebar.number_input("Cost per Channel Piece $", min_value=0.0, value=9.00, step=0.25)
material_markup = st.sidebar.slider("Material Markup %", 0, 100, 15)

# -------------------------
# PROJECT DETAILS
# -------------------------

st.subheader("Project Details")

project_name = st.text_input("Project Name", value="Test Project")
client_name = st.text_input("Client Name", value="Client")

st.divider()

# -------------------------
# WALL INPUTS
# -------------------------

total_wall_length = 0
total_doors = 0
total_door_width = 0

wall_details = []

if needs_framing or needs_drywall:
    st.subheader("Walls")

    num_walls = st.number_input("Number of Walls", min_value=1, value=1)

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        height_ft = st.number_input("Wall Height Feet", min_value=0, value=9, step=1)

    with col_h2:
        height_in = st.number_input("Wall Height Inches", min_value=0, max_value=11, value=0, step=1)

    wall_height = feet_inches_to_decimal(height_ft, height_in)

    for i in range(int(num_walls)):
        st.markdown(f"#### Wall {i + 1}")

        col1, col2 = st.columns(2)

        with col1:
            wall_ft = st.number_input(f"Wall {i + 1} Feet", min_value=0, value=36 if i == 0 else 10, step=1)

        with col2:
            wall_in = st.number_input(f"Wall {i + 1} Inches", min_value=0, max_value=11, value=0, step=1)

        wall_length = feet_inches_to_decimal(wall_ft, wall_in)

        doors_on_wall = st.number_input(
            f"Doors on Wall {i + 1}",
            min_value=0,
            value=0,
            step=1,
            key=f"doors_{i}"
        )

        door_width_sum = 0

        for d in range(int(doors_on_wall)):
            col_d1, col_d2 = st.columns(2)

            with col_d1:
                door_ft = st.number_input(
                    f"Wall {i + 1} Door {d + 1} Width Feet",
                    min_value=0,
                    value=3,
                    step=1,
                    key=f"door_{i}_{d}_ft"
                )

            with col_d2:
                door_in = st.number_input(
                    f"Wall {i + 1} Door {d + 1} Width Inches",
                    min_value=0,
                    max_value=11,
                    value=0,
                    step=1,
                    key=f"door_{i}_{d}_in"
                )

            door_width = feet_inches_to_decimal(door_ft, door_in)
            door_width_sum += door_width

        total_wall_length += wall_length
        total_doors += int(doors_on_wall)
        total_door_width += door_width_sum

        wall_details.append({
            "wall": i + 1,
            "length": wall_length,
            "doors": int(doors_on_wall),
            "door_width": door_width_sum
        })

    total_ft, total_in = decimal_to_feet_inches(total_wall_length)
    st.info(f"Total wall length: {total_ft} ft {total_in} in")

else:
    wall_height = 0
    num_walls = 0

st.divider()

# -------------------------
# FRAMING INPUTS
# -------------------------

system_type = "None"
stud_spacing_inches = 16
channel_spacing_inches = 24
carrying_spacing_ft = 4

if needs_framing:
    st.subheader("Framing System")

    stud_spacing_inches = st.number_input(
        "Stud Spacing Inches",
        min_value=6,
        max_value=48,
        value=16,
        step=1
    )

    system_type = st.selectbox(
        "Wall System",
        [
            "Direct to Metal Studs",
            "Furring Channel",
            "Resilient Channel",
            "Carrying Channel",
            "Shaft Wall"
        ]
    )

    if system_type in ["Furring Channel", "Resilient Channel"]:
        channel_spacing_inches = st.number_input(
            "Channel Spacing Inches",
            min_value=6,
            max_value=48,
            value=24,
            step=1
        )

    if system_type == "Carrying Channel":
        carrying_spacing_ft = st.number_input(
            "Carrying Channel Spacing Feet",
            min_value=2,
            max_value=10,
            value=4,
            step=1
        )

    if system_type == "Shaft Wall":
        st.warning("Shaft wall selected. Confirm CH studs, liner panels, layers, and assembly specs.")

# -------------------------
# DRYWALL INPUTS
# -------------------------

layers_per_side = 0
board_both_sides = False
waste_percent = 0

if needs_drywall:
    st.subheader("Drywall")

    board_both_sides = st.checkbox("Board Both Sides", value=True)

    layers_per_side = st.number_input(
        "Drywall Layers Per Side",
        min_value=1,
        max_value=8,
        value=1,
        step=1
    )

    waste_percent = st.slider("Drywall Waste %", 0, 30, 10)

# -------------------------
# CEILING INPUTS
# -------------------------

include_ceiling = False
ceiling_type = "None"
ceiling_area = 0
ceiling_tiles = 0
main_tee_pieces = 0
cross_tee_pieces = 0
wall_angle_pieces = 0

if needs_ceiling:
    st.subheader("Ceiling")

    ceiling_type = st.selectbox(
        "Ceiling Type",
        [
            "Drywall Ceiling",
            "T-Bar Ceiling",
            "Furring Channel Ceiling",
            "Carrying Channel Ceiling"
        ]
    )

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        ceil_len_ft = st.number_input("Ceiling Length Feet", min_value=0, value=20, step=1)

    with col_c2:
        ceil_len_in = st.number_input("Ceiling Length Inches", min_value=0, max_value=11, value=0, step=1)

    col_c3, col_c4 = st.columns(2)

    with col_c3:
        ceil_wid_ft = st.number_input("Ceiling Width Feet", min_value=0, value=12, step=1)

    with col_c4:
        ceil_wid_in = st.number_input("Ceiling Width Inches", min_value=0, max_value=11, value=0, step=1)

    ceiling_length = feet_inches_to_decimal(ceil_len_ft, ceil_len_in)
    ceiling_width = feet_inches_to_decimal(ceil_wid_ft, ceil_wid_in)
    ceiling_area = ceiling_length * ceiling_width

    if ceiling_type == "T-Bar Ceiling":
        tile_size = st.selectbox("Tile Size", ["2x2", "2x4"])
    else:
        tile_size = "None"

st.divider()

# -------------------------
# CALCULATIONS
# -------------------------

total_studs = 0
track_pieces = 0
track_linear_ft = 0
door_header_track = 0
drywall_sheets = 0
drywall_screws = 0
framing_screws = 0
channel_pieces = 0
channel_linear_ft = 0
channel_note = "No channel."

if needs_framing:
    spacing_ft = stud_spacing_inches / 12

    regular_studs = math.ceil(total_wall_length / spacing_ft)
    end_studs = int(num_walls) * 2

    door_king_studs = total_doors * 2
    door_jack_studs = total_doors * 2

    total_studs = regular_studs + end_studs + door_king_studs + door_jack_studs

    door_header_track = total_door_width

    track_linear_ft = (total_wall_length * 2) + door_header_track
    track_pieces = math.ceil(track_linear_ft / 10)

    framing_screws = total_studs * 4 + total_doors * 20

    if system_type == "Direct to Metal Studs":
        channel_note = "No channel required."

    elif system_type in ["Furring Channel", "Resilient Channel"]:
        channel_spacing_ft = channel_spacing_inches / 12
        rows = math.floor(wall_height / channel_spacing_ft) + 1
        channel_linear_ft = rows * total_wall_length * 1.10
        channel_pieces = math.ceil(channel_linear_ft / 12)
        channel_note = f"{rows} rows @ {channel_spacing_inches} inches spacing."

    elif system_type == "Carrying Channel":
        rows = math.floor(wall_height / carrying_spacing_ft) + 1
        channel_linear_ft = rows * total_wall_length * 1.10
        channel_pieces = math.ceil(channel_linear_ft / 12)
        channel_note = f"{rows} carrying channel rows @ {carrying_spacing_ft} ft spacing."

    elif system_type == "Shaft Wall":
        channel_note = "Shaft wall: verify shaftwall-specific track/channel requirements."

if needs_drywall:
    sides = 2 if board_both_sides else 1
    wall_area_one_side = total_wall_length * wall_height
    drywall_area = wall_area_one_side * sides * layers_per_side

    base_sheets = math.ceil(drywall_area / 32)
    drywall_sheets = math.ceil(base_sheets * (1 + waste_percent / 100))

    drywall_screws = drywall_sheets * 35 * layers_per_side

if needs_ceiling:
    if ceiling_type == "Drywall Ceiling":
        ceiling_drywall_sheets = math.ceil((ceiling_area / 32) * 1.10)
        drywall_sheets += ceiling_drywall_sheets
        drywall_screws += ceiling_drywall_sheets * 35

    elif ceiling_type == "T-Bar Ceiling":
        tile_area = 4 if tile_size == "2x2" else 8
        ceiling_tiles = math.ceil((ceiling_area / tile_area) * 1.10)

        wall_angle_lf = (ceiling_length + ceiling_width) * 2
        wall_angle_pieces = math.ceil(wall_angle_lf / 10)

        main_tee_rows = math.ceil(ceiling_width / 4) + 1
        main_tee_lf = main_tee_rows * ceiling_length
        main_tee_pieces = math.ceil(main_tee_lf / 12)

        cross_tee_pieces = math.ceil(ceiling_area / 4)

    elif ceiling_type in ["Furring Channel Ceiling", "Carrying Channel Ceiling"]:
        ceiling_channel_spacing_ft = 2
        ceiling_channel_rows = math.floor(ceiling_width / ceiling_channel_spacing_ft) + 1
        channel_linear_ft += ceiling_channel_rows * ceiling_length * 1.10
        channel_pieces += math.ceil((ceiling_channel_rows * ceiling_length * 1.10) / 12)

# -------------------------
# PRICING
# -------------------------

if pricing_method == "Per Linear Foot":
    base_labour = total_wall_length * price_per_lf
else:
    base_labour = total_studs * price_per_stud

door_add_on = total_doors * door_price

layer_multiplier = 1 + max(layers_per_side - 1, 0) * 0.5 if needs_drywall else 1

labour_subtotal = (base_labour + door_add_on) * layer_multiplier

material_subtotal = (
    total_studs * stud_cost
    + track_pieces * track_cost
    + drywall_sheets * drywall_cost
    + channel_pieces * channel_cost
)

material_markup_amount = material_subtotal * (material_markup / 100)
material_total = material_subtotal + material_markup_amount

subtotal = labour_subtotal + material_total
profit_amount = subtotal * (profit_margin / 100)
suggested_price = subtotal + profit_amount

# -------------------------
# RESULTS
# -------------------------

st.subheader("Estimate Summary")

col1, col2 = st.columns(2)

with col1:
    if needs_framing:
        st.metric("Metal Studs", f"{total_studs} pcs")
        st.metric("Track", f"{track_pieces} pcs")
        st.metric("Framing Screws", f"{framing_screws}")

with col2:
    if needs_drywall or ceiling_type == "Drywall Ceiling":
        st.metric("Drywall", f"{drywall_sheets} sheets")
        st.metric("Drywall Screws", f"{drywall_screws}")
    if needs_framing or ceiling_type in ["Furring Channel Ceiling", "Carrying Channel Ceiling"]:
        st.metric("Channel", f"{channel_pieces} pcs")

if ceiling_type == "T-Bar Ceiling":
    st.subheader("T-Bar Ceiling")
    st.metric("Tiles", f"{ceiling_tiles}")
    st.metric("Main Tees", f"{main_tee_pieces}")
    st.metric("Cross Tees", f"{cross_tee_pieces}")
    st.metric("Wall Angle", f"{wall_angle_pieces}")

st.divider()

st.subheader("Important Details")

if needs_framing:
    st.write(f"Stud spacing: **{stud_spacing_inches} inches**")
    st.write(f"Door header track included: **{door_header_track:.2f} ft**")
    st.write(f"Total track linear feet: **{track_linear_ft:.2f} ft**")
    st.info(channel_note)

if needs_drywall:
    st.write(f"Drywall layers per side: **{layers_per_side}**")
    if layers_per_side > 1:
        st.warning("Multi-layer/fire-rated wall: extra board, screws, handling, and labour included.")

st.divider()

st.subheader("Pricing")

st.metric("Labour Subtotal", f"${labour_subtotal:.2f}")
st.metric("Material Total", f"${material_total:.2f}")
st.metric("Profit Added", f"${profit_amount:.2f}")
st.metric("Suggested Price", f"${suggested_price:.2f}")

st.divider()

# -------------------------
# QUOTE DOWNLOAD
# -------------------------

quote = f"""
TRADEESTIMATOR QUOTE

Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Project: {project_name}
Client: {client_name}
Scope: {scope}

WALLS
Total Wall Length: {total_wall_length:.2f} ft
Wall Height: {wall_height:.2f} ft
Total Doors: {total_doors}
Total Door Width: {total_door_width:.2f} ft

FRAMING
Stud Spacing: {stud_spacing_inches} inches
Metal Studs: {total_studs}
Track Pieces: {track_pieces}
Track Linear Feet: {track_linear_ft:.2f}
Door Header Track: {door_header_track:.2f}
Framing Screws: {framing_screws}
System: {system_type}
Channel Pieces: {channel_pieces}
Channel Linear Feet: {channel_linear_ft:.2f}
Channel Note: {channel_note}

DRYWALL
Board Both Sides: {board_both_sides}
Layers Per Side: {layers_per_side}
Drywall Sheets: {drywall_sheets}
Drywall Screws: {drywall_screws}

CEILING
Ceiling Type: {ceiling_type}
Ceiling Area: {ceiling_area:.2f}
Tiles: {ceiling_tiles}
Main Tees: {main_tee_pieces}
Cross Tees: {cross_tee_pieces}
Wall Angle: {wall_angle_pieces}

PRICING
Labour Subtotal: ${labour_subtotal:.2f}
Material Total: ${material_total:.2f}
Profit Added: ${profit_amount:.2f}
Suggested Price: ${suggested_price:.2f}
"""

safe_project_name = project_name.replace(" ", "_")
pdf_file = f"{safe_project_name}_quote.pdf"

generate_pdf(pdf_file, quote)

st.subheader("Download Quote")

with open(pdf_file, "rb") as file:
    st.download_button("Download PDF Quote", file, file_name=pdf_file)

st.download_button("Download Text Quote", quote, file_name=f"{safe_project_name}_quote.txt")

st.divider()

# -------------------------
# JOB HISTORY
# -------------------------

st.subheader("Save Job")

if st.button("Save Job to History"):
    file_exists = os.path.exists("job_history.csv")

    with open("job_history.csv", "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Date", "Project", "Client", "Scope", "Wall Length",
                "Studs", "Track", "Drywall", "Channel", "Suggested Price"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            project_name,
            client_name,
            scope,
            total_wall_length,
            total_studs,
            track_pieces,
            drywall_sheets,
            channel_pieces,
            suggested_price
        ])

    st.success("Job saved.")

if os.path.exists("job_history.csv"):
    st.subheader("Job History")
    df = pd.read_csv("job_history.csv")
    st.dataframe(df)

    with open("job_history.csv", "r") as file:
        st.download_button("Download Job History", file, file_name="job_history.csv")