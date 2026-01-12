# Dashboard Tool for the Monitoring of Real Estate Utilization Efficiency 

This project is a demonstration for the **UZH Directorate of Real Estate and Operations (DIB)**. It provides a comprehensive dashboard for analyzing and visualizing room usage statistics at the University of Zurich (UZH).

## Overview

The Room Usage Statistics Dashboard is a Streamlit-based web application that enables interactive analysis of room occupancy data. It offers various visualizations including:

- **Interactive Map**: Geographic visualization of room locations with occupancy metrics
- **Heatmap**: Clustered heatmap showing room usage patterns over time
- **Time Series Analysis**: Detailed occupancy trends for individual rooms
- **Filtering Options**: Semester-based filtering (HS/FS/HS+FS), room type selection, business hours, and workdays

## Features

- Upload and analyze CSV files containing room occupancy data
- Filter data by semester, room type, business hours, and workdays
- Visualize room locations on an interactive map
- Analyze usage patterns with correlation-based clustering
- Track occupancy trends over time for individual rooms
- View detailed statistics including average occupancy, peak occupancy, and usage hours per day

- **Synthetic Dataset** containing comprehensive real estate information:
  - **Sensory Data**: CO₂ concentration, infrared occupancy counting, temperature, light levels, heating status, air conditioning status, and ventilation status
  - **Geolocation Information**: Building locations and GPS coordinates (latitude/longitude) for spatial analysis
  - **Room Metadata**: Room IDs, room types, capacity, and reservation status
  - **Temporal Data**: Dates, weekdays, time stamps, semester periods, and lecture/vacation periods
  - **Usage Metrics**: Occupancy rates and alternative usage indicators

## Technology Stack

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **PyDeck**: Interactive map visualizations
- **NumPy**: Numerical computations

## Usage

### To run the dashboard:

```bash

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### Using requirements.txt

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Dashboard

Once the virtual environment is activated and dependencies are installed, run:

```bash
streamlit run main.py
```

Upload a CSV file containing room occupancy data to begin analysis.

## Data Format

The application expects CSV files with the following columns:

**Room Information:**
- RaumID (Room ID)
- Raumtyp (Room Type)
- Kapazität (Capacity)
- Reserviert (Reserved)

**Sensory Data:**
- CO2 Conc (CO₂ Concentration)
- Infrarot-Zählung (Infrared Occupancy Count)
- Temperatur (Temperature)
- Licht (Light Status)
- Heizung an (Heating On)
- Klimaanlage an (Air Conditioning On)
- Belüftung an (Ventilation On)

**Geolocation:**
- Gebäudelage (Building Location)
- Gebäudekoordinaten (Building Coordinates - latitude,longitude)

**Temporal Data:**
- Datum (Date)
- Wochentag (Weekday)
- Zeit (Time)
- Vorlesungszeit/Semesterferien (Lecture Period/Semester Break)
- Semester (Semester)

**Usage Metrics:**
- Auslastung (Occupancy Rate)
- Alternative Nutzung (Veranstaltungen) (Alternative Usage/Events)

## Project Status

This project was created as a demonstration for the UZH Directorate of Real Estate and Operations for GitHub.
