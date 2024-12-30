import pandas as pd
from geopy.geocoders import Nominatim
import folium
from folium.plugins import FloatImage
import time

def create_company_map(csv_file_path, output_map_path):
    """
    Creates an interactive map of water company locations in Nepal with a title
    and toggleable side panel listing all companies.
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Initialize geolocator
    geolocator = Nominatim(user_agent="nepal_company_mapper")
    
    def get_coordinates(address):
        """
        Get coordinates using multiple search strategies
        Returns: (latitude, longitude, used_query)
        """
        if pd.isna(address):
            return None, None, None

        search_variations = [
            address,
            f"{address}, Nepal",
            address.replace("Ward", "").replace("ward", ""),
            address.split(',')[0] + ", Nepal" if ',' in address else address,
            address.split(',')[-1].strip() + ", Nepal" if ',' in address else address
        ]
        
        search_variations = list(dict.fromkeys(search_variations))
        
        for query in search_variations:
            try:
                time.sleep(1)
                location = geolocator.geocode(query)
                if location:
                    print(f"Geocoded '{query}' successfully.")
                    return location.latitude, location.longitude, query
            except Exception as e:
                print(f"Error geocoding '{query}': {str(e)}")
                continue
        
        return None, None, None

    print("Geocoding addresses...")
    results = []
    for idx, row in df.iterrows():
        lat, lon, used_query = get_coordinates(row['Location'])
        results.append((lat, lon, used_query))
        if (idx + 1) % 5 == 0:
            print(f"Processed {idx + 1}/{len(df)} addresses...")

    df['Latitude'], df['Longitude'], df['Used_Query'] = zip(*results)
    
    # Create a map centered around Nepal
    nepal_map = folium.Map(
        location=[28.3949, 84.1240],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; 
                left: 50px; 
                width: 300px; 
                height: 60px; 
                z-index: 1000;
                background-color: white; 
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 0 5px rgba(0,0,0,0.2);">
        <h3 style="margin: 0; text-align: center; color: #333;">
            Nepal Water Companies
        </h3>
    </div>
    '''
    nepal_map.get_root().html.add_child(folium.Element(title_html))
    
    # Create side panel with company list
    side_panel_html = '''
    <div id="side-panel" style="
        position: fixed;
        top: 80px;
        left: 10px;
        width: 250px;
        max-height: 70%;
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.2);
        overflow-y: auto;
        z-index: 1000;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <h4 style="margin: 0;">Companies List</h4>
            <button onclick="togglePanel()" style="border: none; background: none; cursor: pointer;">
                ➖
            </button>
        </div>
        <div id="company-list">
    '''
    
    # Add companies to the side panel
    for idx, row in df.iterrows():
        if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
            side_panel_html += f'''
                <div style="margin-bottom: 8px; padding: 5px; border-bottom: 1px solid #eee;">
                    <strong>{row['Name']}</strong><br>
                    <small>{row['Location']}</small>
                </div>
            '''
    
    side_panel_html += '''
        </div>
    </div>
    
    <script>
    function togglePanel() {
        var panel = document.getElementById('company-list');
        var button = document.querySelector('#side-panel button');
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            button.innerHTML = '➖';
        } else {
            panel.style.display = 'none';
            button.innerHTML = '➕';
        }
    }
    </script>
    '''
    
    nepal_map.get_root().html.add_child(folium.Element(side_panel_html))
    
    # Add markers with enhanced popups
    valid_locations = 0
    for idx, row in df.iterrows():
        if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
            popup_html = f"""
                <div style="min-width: 200px;">
                    <h4 style="margin: 4px 0;">{row['Name']}</h4>
                    <p style="margin: 4px 0;"><b>Location:</b> {row['Location']}</p>
                    <p style="margin: 4px 0; font-size: 0.8em; color: #666;">
                        <b>Found using:</b> {row['Used_Query']}
                    </p>
                </div>
            """
            
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=row['Name']
            ).add_to(nepal_map)
            valid_locations += 1
    
    # Save the map
    nepal_map.save(output_map_path)
    
    # Print statistics and save files
    print(f"\nMap creation completed:")
    print(f"Total locations processed: {len(df)}")
    print(f"Successfully mapped locations: {valid_locations}")
    print(f"Failed to map locations: {len(df) - valid_locations}")
    
    unmapped = df[df['Latitude'].isnull()][['Name', 'Location']]
    if not unmapped.empty:
        unmapped_file = csv_file_path.replace('.csv', '_unmapped.csv')
        unmapped.to_csv(unmapped_file, index=False)
        print(f"\nUnmapped locations saved to: {unmapped_file}")
    
    output_csv = csv_file_path.replace('.csv', '_with_coordinates.csv')
    df.to_csv(output_csv, index=False)
    print(f"Updated CSV with coordinates saved to: {output_csv}")
    
    return nepal_map

if __name__ == "__main__":
    create_company_map(
        csv_file_path="water_companies.csv",
        output_map_path="index.html"
    )