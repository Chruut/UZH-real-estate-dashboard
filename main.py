import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pydeck as pdk

st.set_page_config(page_title="UZH Raumauslastung Dashboard", page_icon="🏢", layout="wide")

def load_data_from_file(uploaded_file):
    df = pd.read_csv(uploaded_file)
    
    # Convert Auslastung to percentage and rename column
    df['Auslastung (%)'] = (df['Auslastung'] * 100).round(1)
    
    print(f"Data loaded from uploaded file with {len(df)} records")
    return df

def main():
    st.title("Nutzung der räumlichen Ressourcen der UZH")
    
    # CSV file upload/selection
    uploaded_file = st.file_uploader("CSV-Datei hochladen", type=['csv'])
    
    if uploaded_file is not None:
        df = load_data_from_file(uploaded_file)
        
        if df.empty:
            st.error("No data found!")
            return
    else:
        st.info("Bitte laden Sie eine CSV-Datei hoch, um das Dashboard zu verwenden.")
        return
    
    # Create three columns for the filters
    col1, col2, col3 = st.columns(3)
    
    # Semester period filter in second column
    with col2:
        semester_option = st.radio(
            "Semester:",
            ["HS", "FS", "HS+FS"],
            index=2
        )
    
    # Raumtyp filter in first column
    with col1:
        room_types = ["Alle"] + sorted(df['Raumtyp'].unique().tolist())
        room_type = st.selectbox("Raumtyp:", room_types)
    
    # Time and day filters in third column
    with col3:
        show_business_hours = st.checkbox("Geschäftszeiten (8-20 Uhr)", value=False)
        show_workdays = st.checkbox("Werktage (Mo-Fr)", value=False)
    
    # Apply filters
    df_filtered = df.copy()
    
    # Apply business hours filter if button is pressed
    if show_business_hours:
        df_filtered = df_filtered[pd.to_datetime(df_filtered['Zeit'], format='%H:%M').dt.hour.between(8, 20)]
        print("Time filter applied - showing data between 8:00-20:00")
    
    # Apply workdays filter if button is pressed
    if show_workdays:
        werktage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
        df_filtered = df_filtered[df_filtered['Wochentag'].isin(werktage)]
        print("Workdays filter applied - showing data for Mon-Fri only")
    
    # Apply semester filter
    if semester_option != "HS+FS":
        semester_mapping = {"HS": "Herbstsemester", "FS": "Frühlingssemester"}
        df_filtered = df_filtered[df_filtered['Semester'] == semester_mapping[semester_option]].copy()
        print(f"Semester filter applied - showing {semester_option} data")
    
    # Apply Raumtyp filter
    if room_type != "Alle":
        df_filtered = df_filtered[df_filtered['Raumtyp'] == room_type]
        print(f"Raumtyp filter applied - showing {room_type} data")

    # Convert Datum to datetime first
    df_filtered['Datum'] = pd.to_datetime(df_filtered['Datum'])
    
    # Determine semester start date for all plots
    if semester_option == "HS":
        semester_start = pd.Timestamp(df_filtered['Datum'].dt.year.min(), 8, 14)  # August 14th (HS start)
    elif semester_option == "FS":
        semester_start = pd.Timestamp(df_filtered['Datum'].dt.year.max(), 2, 1)  # February 1st (FS start)
    else:  # HS+FS
        semester_start = pd.Timestamp(df_filtered['Datum'].dt.year.min(), 8, 14)  # August 14th

    # === 1. MAP AND KPIs (directly after filters) ===
    st.write("---")
    st.subheader("Raumauslastung auf der Karte")
    
    try:
        # Create a room-level dataframe (not aggregated by location)
        df_room_data = df_filtered.copy()
        
        # Calculate room-level statistics
        room_summary = []
        for room_id in df_room_data['RaumID'].unique():
            room_data = df_room_data[df_room_data['RaumID'] == room_id]
            
            # Get coordinates (first entry for this room)
            coord_str = room_data['Gebäudekoordinaten'].iloc[0]
            lat, lon = coord_str.split(',')
            lat, lon = float(lat), float(lon)
            
            # Calculate room statistics
            avg_occupancy = room_data['Auslastung (%)'].mean()
            peak_occupancy = room_data['Auslastung (%)'].max()
            
            # Calculate usage hours per day (hours where occupancy > 0)
            usage_entries = room_data[room_data['Auslastung (%)'] > 0]
            total_days = room_data['Datum'].nunique()
            total_usage_hours = len(usage_entries) * 2  # Each entry represents 2 hours
            avg_usage_hours_per_day = total_usage_hours / total_days if total_days > 0 else 0
            
            # Get room info
            room_type = room_data['Raumtyp'].iloc[0]
            capacity = room_data['Kapazität'].iloc[0]
            location = room_data['Gebäudelage'].iloc[0]
            
            room_summary.append({
                'RaumID': room_id,
                'lat': lat,
                'lon': lon,
                'Durchschnittliche_Auslastung': avg_occupancy,
                'Peak_Auslastung': peak_occupancy,
                'Nutzungsstunden_pro_Tag': avg_usage_hours_per_day,
                'Raumtyp': room_type,
                'Kapazität': capacity,
                'Gebäudelage': location,
                'size': max(5, min(25, avg_occupancy * 0.8))  # Size based on occupancy (5-25px)
            })
        
        df_map = pd.DataFrame(room_summary)
        
        if not df_map.empty:
            # Prepare data for pydeck map with enhanced interactivity
            df_map['radius'] = df_map['Durchschnittliche_Auslastung'] * 1.5 + 15  # Smaller points (15-165 radius)
            
            # Calculate color range for normalization
            min_occupancy = df_map['Durchschnittliche_Auslastung'].min()
            max_occupancy = df_map['Durchschnittliche_Auslastung'].max()
            
            # Create RGB colors as separate columns for pydeck
            df_map['color_r'] = df_map['Durchschnittliche_Auslastung'].apply(
                lambda x: int(255 * ((x - min_occupancy) / (max_occupancy - min_occupancy) if max_occupancy != min_occupancy else 0.5))
            )
            df_map['color_g'] = df_map['Durchschnittliche_Auslastung'].apply(
                lambda x: int(255 * (1 - abs(((x - min_occupancy) / (max_occupancy - min_occupancy) if max_occupancy != min_occupancy else 0.5) - 0.5) * 2))
            )
            df_map['color_b'] = df_map['Durchschnittliche_Auslastung'].apply(
                lambda x: int(255 * (1 - ((x - min_occupancy) / (max_occupancy - min_occupancy) if max_occupancy != min_occupancy else 0.5)))
            )
            
            # Create columns for layout: KPIs left, Map right
            kpi_col, map_col = st.columns([1, 2])
            
            with kpi_col:
                st.subheader("Übersichts-Statistiken zum Raum")
                
                # Room selection dropdown
                selected_room = st.selectbox(
                    "Raum auswählen:",
                    options=df_map['RaumID'].tolist(),
                    index=0,
                    key="room_selector"
                )
                
                if selected_room:
                    room_info = df_map[df_map['RaumID'] == selected_room].iloc[0]
                    
                    # Display KPIs for selected room
                    st.metric(
                        "Durchschnittliche Auslastung",
                        f"{room_info['Durchschnittliche_Auslastung']:.1f}%"
                    )
                    st.metric(
                        "Peak Auslastung",
                        f"{room_info['Peak_Auslastung']:.1f}%"
                    )
                    st.metric(
                        "Nutzungsstunden/Tag",
                        f"{room_info['Nutzungsstunden_pro_Tag']:.1f}h"
                    )
                

            
            with map_col:
                # Create the pydeck layer
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=df_map,
                    get_position=["lon", "lat"],
                    get_color=["color_r", "color_g", "color_b", 180],
                    get_radius="radius",
                    radius_scale=1,
                    radius_min_pixels=10,
                    radius_max_pixels=50,
                    pickable=True,
                    auto_highlight=True,
                )
                
                # Set up the viewport
                view_state = pdk.ViewState(
                    latitude=df_map['lat'].mean(),
                    longitude=df_map['lon'].mean(),
                    zoom=11,
                    pitch=0,
                    bearing=0
                )
                
                # Create the deck with dark theme
                deck = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={
                        "html": "<b>{RaumID}</b><br/>"
                               "Typ: {Raumtyp}<br/>"
                               "Standort: {Gebäudelage}",
                        "style": {"backgroundColor": "steelblue", "color": "white"}
                    },
                    map_style="mapbox://styles/mapbox/dark-v10",
                    height=500
                )
                
                # Display the map
                st.pydeck_chart(deck, use_container_width=True)
            
            # Top/Bottom performing rooms in horizontal layout under the map
            st.write("---")
            perf_col1, perf_col2 = st.columns(2)
            
            with perf_col1:
                # Top 3 rooms
                top_rooms = df_map.nlargest(3, 'Durchschnittliche_Auslastung')
                st.write("**Höchste Auslastung:**")
                for _, room in top_rooms.iterrows():
                    st.write(f"• {room['RaumID']}: {room['Durchschnittliche_Auslastung']:.1f}%")
            
            with perf_col2:
                # Bottom 3 rooms
                bottom_rooms = df_map.nsmallest(3, 'Durchschnittliche_Auslastung')
                st.write("**Niedrigste Auslastung:**")
                for _, room in bottom_rooms.iterrows():
                    st.write(f"• {room['RaumID']}: {room['Durchschnittliche_Auslastung']:.1f}%")
        
        else:
            st.warning("Keine Daten für die Kartenanzeige verfügbar.")
            selected_room = None  # No room available if map fails
    
    except Exception as e:
        st.error(f"Fehler bei der Erstellung der Raum-Karte: {str(e)}")
        print(f"Error creating room map: {e}")
        selected_room = None  # No room available if error occurs



    # === 3. CLUSTER HEATMAP ===
    st.write("---")
    st.subheader("Heatmap Raumauslastung")
    
    try:
        # Create cluster analysis dataframe
        df_cluster = df_filtered.copy()
        
        if len(df_cluster) > 0:
            # Create half-day identifier for clustering
            df_cluster['Half_Day'] = df_cluster.apply(
                lambda row: f"{row['Datum']}_{('VM' if pd.to_datetime(row['Zeit'], format='%H:%M').hour <= 12 else 'NM')}",
                axis=1
            )
            
            # Create pivot table for clustering analysis
            pivot_data = df_cluster.pivot_table(
                index='RaumID',
                columns='Half_Day',
                values='Auslastung (%)',
                aggfunc='mean',
                fill_value=0
            )
            
            print(f"Created pivot table with {len(pivot_data.index)} rooms and {len(pivot_data.columns)} half-days")
            
            if len(pivot_data) > 1:
                # Calculate correlation matrix between rooms
                correlation_matrix = pivot_data.T.corr()
                
                # Sort rooms by average correlation (similarity clustering)
                avg_correlations = correlation_matrix.mean(axis=1).sort_values(ascending=False)
                clustered_order = avg_correlations.index.tolist()
                
                # Reorder pivot data based on clustering
                pivot_clustered = pivot_data.reindex(clustered_order)
                
                # Create datetime objects for x-axis to match the bar plot
                half_day_dates = []
                for half_day in pivot_clustered.columns:
                    date_str = half_day.split('_')[0]
                    half_day_dates.append(pd.to_datetime(date_str))
                
                # Sort by date to ensure proper timeline
                sorted_indices = sorted(range(len(half_day_dates)), key=lambda i: half_day_dates[i])
                x_axis_dates = [half_day_dates[i] for i in sorted_indices]
                pivot_clustered = pivot_clustered.iloc[:, sorted_indices]
                
                # Create the heatmap
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=pivot_clustered.values,
                    x=x_axis_dates,  # Use actual datetime objects like in bar plot
                    y=pivot_clustered.index,
                    colorscale='RdYlBu_r',
                    hoverongaps=False,
                    hovertemplate='<b>Raum</b>: %{y}<br>' +
                                 '<b>Datum</b>: %{x|%Y-%m-%d}<br>' +  # Changed to match bar plot
                                 '<b>Auslastung</b>: %{z:.1f}%<br>' +
                                 '<extra></extra>'
                ))
                
                # Update layout to match the bar plot's x-axis settings
                fig_heatmap.update_layout(
                    xaxis_title="Zeitverlauf",
                    yaxis_title="Raum (nach Ähnlichkeit gruppiert)",
                    height=max(400, len(pivot_clustered) * 25),
                    xaxis=dict(
                        dtick='604800000',  # Weekly ticks (7 days in milliseconds)
                        tickformat='%Y-%m-%d',  # Date format
                        range=[semester_start, df_filtered['Datum'].max()],  # Same range as bar plot
                        tick0=semester_start,  # Start ticks from semester start (Monday)
                        tickmode='linear'
                    )
                )
                
                # Add horizontal lines to separate rooms
                for i in range(len(pivot_clustered.index) - 1):
                    fig_heatmap.add_hline(
                        y=i + 0.5,
                        line=dict(color="rgba(255,255,255,0.6)", width=1),
                        layer="above"
                    )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
            elif len(pivot_data) == 1:
                # Handle single room case
                room_name = pivot_data.index[0]
                st.info(f"Nur ein Raum ({room_name}) gefunden. Zeige einfache Zeitreihe statt Clustering.")
                
                # Create simple heatmap for single room
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=[pivot_data.iloc[0].values],
                    x=pivot_data.columns,
                    y=[room_name],
                    colorscale='RdYlBu_r',
                    hoverongaps=False
                ))
                
                fig_heatmap.update_layout(
                    title=f"Auslastung für {room_name}",
                    xaxis_title="Half-Day",
                    yaxis_title="Raum",
                    height=200
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            else:
                st.warning("Nicht genügend Daten für Clustering-Analyse verfügbar.")
        
        else:
            st.warning("Keine Daten für Heatmap verfügbar.")
    
    except Exception as e:
        st.error(f"Fehler bei der Erstellung der Cluster-Heatmap: {str(e)}")
        print(f"Error creating cluster heatmap: {e}")

# === 2. BAR PLOT FOR TIME SERIES ===
    st.write("---")
    
    # Get selected room from session state or use default
    if 'selected_room' in locals() and selected_room:
        display_room = selected_room
        st.subheader(f"Raumauslastung im Zeitverlauf: {selected_room}")
    else:
        # Fallback if no room selected
        available_rooms = df_filtered['RaumID'].unique()
        if len(available_rooms) > 0:
            display_room = available_rooms[0]
            st.subheader(f"Raumauslastung im Zeitverlauf: {display_room}")
        else:
            st.subheader("Raumauslastung im Zeitverlauf")
            display_room = None
    
    try:
        if display_room:
            # Filter data for the selected room only
            df_room_filtered = df_filtered[df_filtered['RaumID'] == display_room].copy()
            
            if len(df_room_filtered) == 0:
                st.warning(f"Keine Daten für Raum {display_room} verfügbar.")
            else:
                # Create half-day averages dataframe for selected room only
                df_room_filtered['Tageszeit'] = pd.to_datetime(df_room_filtered['Zeit'], format='%H:%M').dt.hour.apply(
                    lambda x: 'Vormittag' if x <= 12 else 'Nachmittag'
                )
                
                print(f"Creating time series for room {display_room}")
                print(f"Setting semester start date to {semester_start.strftime('%Y-%m-%d')}")
                
                # Calculate time shift needed
                actual_start = df_room_filtered['Datum'].min()
                time_shift = semester_start - actual_start
                
                # Shift dates if needed
                if time_shift.days != 0:
                    print(f"Shifting dates by {time_shift.days} days to align with semester start")
                    df_room_filtered['Datum'] = df_room_filtered['Datum'] + time_shift
                
                # Filter data to start from semester start
                df_room_filtered = df_room_filtered[df_room_filtered['Datum'] >= semester_start]
                
                # For individual room, we don't need to group by room since it's already filtered
                df_halfday = df_room_filtered.groupby(['Datum', 'Tageszeit'])['Auslastung (%)'].mean().reset_index()
                df_halfday = df_halfday.rename(columns={'Auslastung (%)': 'Auslastung (%)'})
                
                print(f"Created time series for {display_room} starting from {semester_start.strftime('%Y-%m-%d')}")
                
                # Create the bar plot with custom colors
                fig = px.bar(df_halfday,
                            x='Datum',
                            y='Auslastung (%)',
                            color='Tageszeit',
                            barmode='group',
                            color_discrete_map={
                                'Vormittag': '#1f77b4',  # Default blue
                                'Nachmittag': '#8B0000'  # Dark red
                            })
                
                # Customize the plot
                fig.update_traces(
                    opacity=0.8,  # Add light transparency (80% opacity)
                    hovertemplate='<b>Datum</b>: %{x|%Y-%m-%d}<br>' +
                                 f'<b>{display_room} Auslastung (%)</b>: %{{y:.1f}}%<br>' +
                                 '<b>Tageszeit</b>: %{customdata}<br>'
                )
                
                fig.update_layout(
                    xaxis_title="Datum",
                    yaxis_title="Auslastung (%)",
                    legend_title="Tageszeit",
                    xaxis=dict(
                        dtick='604800000',  # Weekly ticks (7 days in milliseconds)
                        tickformat='%Y-%m-%d',  # Format as YYYY-MM-DD
                        range=[semester_start, df_room_filtered['Datum'].max()],  # Set range from semester start
                        tick0=semester_start,  # Start ticks from semester start (Monday)
                        tickmode='linear'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Kein Raum für die Zeitverlauf-Analyse verfügbar.")
    
    except Exception as e:
        st.error(f"Fehler bei der Erstellung des Zeitverlauf-Diagramms: {str(e)}")
        print(f"Error creating time series plot: {e}")


    
    # === 4. DATA TABLE ===
    st.write("---")
    st.subheader("Gefilterte Daten als Tabelle")
    
    if not df_filtered.empty:
        st.write(df_filtered)
    else:
        st.warning("Keine Daten entsprechen den aktuellen Filterkriterien.")

if __name__ == "__main__":
    main()
