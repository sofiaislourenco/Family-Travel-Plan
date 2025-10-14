import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import google.generativeai as genai
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Family Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Title and description
st.title("✈️ Family Travel Planner")
st.markdown("""
Plan your perfect family vacation! Enter your destination, trip duration, and family details 
to get personalized activity recommendations and an interactive map with all the places to visit.
""")

# Sidebar for user inputs
st.sidebar.header("Trip Details")

# Destination input
destination = st.sidebar.text_input(
    "Destination",
    placeholder="e.g., Paris, France",
    help="Enter the city AND country for best results (e.g., 'Athens, Greece' not just 'Athens')"
)

# Number of days
num_days = st.sidebar.number_input(
    "Number of Days",
    min_value=1,
    max_value=30,
    value=3,
    help="How many days will you be traveling?"
)

# Kids toggle
with_kids = st.sidebar.checkbox("Traveling with kids?")

# Kids ages (conditional)
kids_ages = []
if with_kids:
    num_kids = st.sidebar.number_input(
        "Number of children",
        min_value=1,
        max_value=10,
        value=1
    )
    
    st.sidebar.markdown("**Children's ages:**")
    for i in range(int(num_kids)):
        age = st.sidebar.number_input(
            f"Child {i+1} age",
            min_value=0,
            max_value=18,
            value=5,
            key=f"kid_age_{i}"
        )
        kids_ages.append(age)

# Generate button
st.sidebar.markdown("---")
generate_button = st.sidebar.button("🗺️ Generate Travel Plan", type="primary", use_container_width=True)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Clear Cache", help="Clear geocoding cache if map markers aren't showing"):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared! Generate a new plan.")
    
st.sidebar.caption("✅ Powered by Google Gemini AI & Google Maps")
st.sidebar.caption("⏱️ Map loading: ~1.5 sec per location (rate limits)")

# Helper Functions
# Track last request time for rate limiting
_last_geocode_time = [0]  # Use list to make it mutable in nested scope

@st.cache_data(ttl=3600)  # Cache for 1 hour
def _geocode_cached(location_name):
    """Internal cached geocoding function."""
    # Use Nominatim (OpenStreetMap) - free and reliable
    try:
        geolocator = Nominatim(user_agent="family_travel_planner_app_v3", timeout=15)
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        return None
    except Exception as e:
        print(f"Geocoding error for {location_name}: {str(e)}")
        return None

def get_location_coordinates(location_name):
    """Get coordinates for a given location name with rate limiting."""
    import time
    
    # Enforce rate limiting: wait at least 1.5 seconds between requests
    current_time = time.time()
    time_since_last = current_time - _last_geocode_time[0]
    if time_since_last < 1.5:
        sleep_time = 1.5 - time_since_last
        time.sleep(sleep_time)
    
    result = _geocode_cached(location_name)
    _last_geocode_time[0] = time.time()
    return result

def generate_travel_plan(destination, num_days, with_kids, kids_ages):
    """Generate a travel plan using Google Gemini."""
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        st.error("⚠️ Gemini API key not found. Please add GEMINI_API_KEY to your .env file.")
        return None
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Build the prompt
        kids_info = ""
        kids_challenge_info = ""
        if with_kids and kids_ages:
            ages_str = ", ".join([str(age) for age in kids_ages])
            kids_info = f" The family is traveling with {len(kids_ages)} child(ren) aged {ages_str} years old. Please suggest kid-friendly activities appropriate for these ages."
            kids_challenge_info = f"""
                    "challenge": "A fun, age-appropriate challenge or scavenger hunt item for kids aged {ages_str} at this location (e.g., 'Find 3 different types of columns' or 'Count how many statues you can see')","""
        
        prompt = f"""Create a detailed {num_days}-day travel itinerary for {destination}.{kids_info}

For each day, provide:
1. 3-5 specific activities or places to visit
2. Brief description of each activity
3. Approximate time to spend at each location
{"4. A fun challenge or game for kids at each location" if with_kids else ""}

IMPORTANT: For the "location" field - Keep it SIMPLE and SHORT for geocoding:
- Format: "Landmark Name, City, Country" (3 parts ONLY)
- Use SHORT, COMMONLY-KNOWN names (e.g., "Aquatis" not "Aquatis Aquarium-Vivarium Lausanne")
- Use local language but PREFER SHORT VERSIONS over formal long names
- NO street addresses, building numbers, postal codes, formal titles, or extra descriptions
- Examples GOOD (short & simple):
  * "Sagrada Familia, Barcelona, Spain" (not "Basílica de la Sagrada Família")
  * "Aquatis, Lausanne, Switzerland" (not "Aquatis Aquarium-Vivarium")
  * "Ouchy, Lausanne, Switzerland" (not "Promenade d'Ouchy")
  * "Jardin Botanique, Lausanne, Switzerland" (not "Musée et Jardins Botaniques Lausannois")
  * "Cathédrale de Lausanne, Lausanne, Switzerland" (French name, not "Lausanne Cathedral")
  * "Torre de Belém, Lisbon, Portugal" (short, well-known)
  * "Park Güell, Barcelona, Spain" (not "Parc Güell de Barcelona")
- Examples BAD (too long/detailed):
  * "Basílica de la Sagrada Família, Carrer de Mallorca, 401, Barcelona, Spain" (has address!)
  * "Aquatis Aquarium-Vivarium Lausanne, Route de Berne 144, Lausanne, Switzerland" (too long!)
  * "Promenade d'Ouchy, Lausanne, Switzerland" (use just "Ouchy")
  * "Lausanne Cathedral, Lausanne, Switzerland" (use French: "Cathédrale de Lausanne")
  * "Tram 28, Lisbon, Portugal" (route, not a place)

Please format the response as a JSON object with the following structure:
{{
    "days": [
        {{
            "day": 1,
            "activities": [
                {{
                    "name": "Activity/Place Name",
                    "description": "Brief description",
                    "duration": "Suggested duration",
                    "location": "Specific landmark or address, {destination}",{kids_challenge_info if with_kids else ""}
                }}
            ]
        }}
    ]
}}

Make sure all locations are real, specific places in {destination} with actual addresses or well-known landmarks.
Always include the full city and country in each location field.
Respond ONLY with the JSON object, no additional text."""

        response = model.generate_content(prompt)
        
        # Parse the response
        content = response.text
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
            
        travel_plan = json.loads(content)
        return travel_plan
        
    except Exception as e:
        st.error(f"Error generating travel plan: {str(e)}")
        return None

def create_map_with_route(destination, travel_plan, status_placeholder=None, progress_bar=None, debug_callback=None):
    """Create an interactive map with markers for all activities."""
    # Get destination coordinates - try to use first activity location if available for better accuracy
    dest_coords = None
    
    # First, try to get coordinates from the first activity location (which should have full address)
    if travel_plan and 'days' in travel_plan and len(travel_plan['days']) > 0:
        first_day = travel_plan['days'][0]
        if 'activities' in first_day and len(first_day['activities']) > 0:
            first_location = first_day['activities'][0].get('location', '')
            if first_location:
                dest_coords = get_location_coordinates(first_location)
    
    # Fallback to destination name
    if not dest_coords:
        dest_coords = get_location_coordinates(destination)
    
    if not dest_coords:
        st.error(f"Could not find coordinates for {destination}")
        return None
    
    # Get Google Maps API key
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Create base map with Google Maps
    travel_map = folium.Map(
        location=dest_coords,
        zoom_start=13,
        tiles=None
    )
    
    # Add Google Maps tile layer
    if google_maps_key:
        folium.TileLayer(
            tiles=f'https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={google_maps_key}',
            attr='Google Maps',
            name='Google Maps',
            overlay=False,
            control=True
        ).add_to(travel_map)
    else:
        # Fallback to OpenStreetMap if no API key
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(travel_map)
    
    # Track all locations
    all_locations = []
    
    # Color scheme for different days
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
              'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'pink']
    
    # Add markers for each activity
    markers_added = 0
    failed_locations = []
    if travel_plan and 'days' in travel_plan:
        # Count total activities for progress
        total_activities = sum(len(day.get('activities', [])) for day in travel_plan['days'])
        activity_count = 0
        
        msg = f"Starting to geocode {total_activities} activities for {destination}"
        print(f"\n📍 {msg}")
        if debug_callback:
            debug_callback(msg)
        
        for day_idx, day in enumerate(travel_plan['days']):
            day_num = day.get('day', day_idx + 1)
            color = colors[day_idx % len(colors)]
            
            day_msg = f"Day {day_num}"
            print(f"\n--- {day_msg} ---")
            if debug_callback:
                debug_callback(f"--- {day_msg} ---")
            
            if 'activities' in day:
                for act_idx, activity in enumerate(day['activities']):
                    location_name = activity.get('location', activity.get('name', ''))
                    activity_count += 1
                    
                    # Update progress
                    if progress_bar:
                        progress_bar.progress(activity_count / total_activities)
                    if status_placeholder:
                        status_placeholder.info(f"📍 Geocoding location {activity_count}/{total_activities}: {location_name[:50]}...")
                    
                    # Try to geocode the location
                    try:
                        # Clean up location name - remove parentheses, detailed addresses, etc.
                        import re
                        clean_location = location_name
                        
                        # Remove parenthetical content
                        clean_location = re.sub(r'\([^)]*\)', '', clean_location)
                        
                        # Remove prefixes like "Inside", "Near", "At", etc.
                        clean_location = re.sub(r'^(Inside|Near|At|In)\s+', '', clean_location, flags=re.IGNORECASE)
                        
                        # Extract just the landmark name (before first comma) + city + country
                        # This removes detailed addresses
                        parts = clean_location.split(',')
                        if len(parts) >= 3:
                            # Keep only: landmark, city, country (skip street addresses)
                            landmark = parts[0].strip()
                            # Last part should be country, second-to-last might be city
                            country = parts[-1].strip()
                            
                            # Look for the destination city in the parts
                            city = None
                            for part in parts:
                                if destination.lower() in part.lower() or any(city_name in part for city_name in ['Barcelona', 'Lisbon', 'Athens', 'Paris', 'Rome', 'Madrid', 'Porto']):
                                    city = part.strip()
                                    break
                            
                            if not city:
                                city = parts[-2].strip()
                            
                            clean_location = f"{landmark}, {city}, {country}"
                        
                        # Remove postal codes (5 digits)
                        clean_location = re.sub(r'\b\d{5}\b', '', clean_location)
                        
                        # Remove extra whitespace
                        clean_location = re.sub(r'\s+', ' ', clean_location).strip()
                        clean_location = re.sub(r',\s*,', ',', clean_location)  # Remove double commas
                        
                        # Final format
                        full_location = clean_location
                        
                        print(f"[{activity_count}/{total_activities}] Attempting to geocode: {full_location}")
                        coords_result = get_location_coordinates(full_location)
                        
                        # If no result, try alternative formats
                        if not coords_result:
                            # Try just the landmark name without full address
                            alt_location = f"{activity.get('name', '')}, {destination}"
                            print(f"  └─ Trying alternative: {alt_location}")
                            coords_result = get_location_coordinates(alt_location)
                        
                        if coords_result:
                            coords = coords_result
                            all_locations.append(coords)
                            markers_added += 1
                            success_msg = f"✓ Marker {markers_added}: {location_name[:40]}"
                            print(f"  {success_msg}")
                            if debug_callback:
                                debug_callback(success_msg)
                            
                            # Create popup content
                            challenge_html = ""
                            if 'challenge' in activity:
                                challenge_html = f'<div style="background-color: #e3f2fd; padding: 5px; margin-top: 5px; border-radius: 3px; font-size: 11px;"><b>🎯 Challenge:</b> {activity["challenge"][:80]}...</div>'
                            
                            popup_html = f"""
                            <div style="font-family: Arial; width: 220px;">
                                <h4 style="color: {color};">Day {day_num}</h4>
                                <b>{activity.get('name', 'Activity')}</b><br>
                                <i>{activity.get('duration', 'N/A')}</i><br>
                                <p style="font-size: 12px;">{activity.get('description', '')[:100]}...</p>
                                {challenge_html}
                            </div>
                            """
                            
                            folium.Marker(
                                coords,
                                popup=folium.Popup(popup_html, max_width=280),
                                tooltip=f"Day {day_num}: {activity.get('name', 'Activity')}",
                                icon=folium.Icon(color=color, icon='info-sign', prefix='glyphicon')
                            ).add_to(travel_map)
                        else:
                            fail_msg = f"✗ Failed: {location_name[:40]}"
                            print(f"  {fail_msg}")
                            if debug_callback:
                                debug_callback(fail_msg)
                            failed_locations.append(location_name)
                    except Exception as e:
                        # Log error but continue
                        print(f"✗ Failed to geocode: {location_name} - {str(e)}")
                        continue
    
    # Fit map to show all markers
    if all_locations:
        travel_map.fit_bounds(all_locations)
    
    print(f"\n🗺️ Map generation complete: {markers_added} markers added out of {total_activities} activities")
    if failed_locations:
        print(f"Failed locations: {', '.join(failed_locations)}")
    
    return travel_map, markers_added, total_activities, failed_locations

# Main logic
if generate_button:
    if not destination:
        st.warning("Please enter a destination!")
    else:
        with st.spinner("🧳 Planning your perfect trip..."):
            # Generate travel plan
            travel_plan = generate_travel_plan(destination, num_days, with_kids, kids_ages)
            
            if travel_plan:
                # Store in session state
                st.session_state['travel_plan'] = travel_plan
                st.session_state['destination'] = destination
                st.session_state['num_days'] = num_days

# Display results if available
if 'travel_plan' in st.session_state:
    travel_plan = st.session_state['travel_plan']
    destination = st.session_state['destination']
    
    st.success(f"✅ Your {st.session_state['num_days']}-day travel plan for {destination} is ready!")
    
    # Debug expander
    with st.expander("🔍 Debug: View Raw Plan Data"):
        st.json(travel_plan)
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📋 Itinerary")
        
        if 'days' in travel_plan:
            for day in travel_plan['days']:
                day_num = day.get('day', 1)
                with st.expander(f"**Day {day_num}**", expanded=True):
                    if 'activities' in day:
                        for idx, activity in enumerate(day['activities'], 1):
                            st.markdown(f"**{idx}. {activity.get('name', 'Activity')}**")
                            st.markdown(f"*Duration: {activity.get('duration', 'N/A')}*")
                            st.markdown(f"{activity.get('description', '')}")
                            if 'location' in activity:
                                st.caption(f"📍 {activity['location']}")
                            if 'challenge' in activity:
                                st.info(f"🎯 **Kids Challenge:** {activity['challenge']}")
                            st.markdown("---")
    
    with col2:
        st.header("🗺️ Interactive Map")
        
        map_status = st.empty()
        progress_bar = st.progress(0)
        debug_text = st.empty()
        map_status.info("📍 Loading map locations... This may take a moment due to rate limits.")
        
        # Create a callback to update debug info
        debug_messages = []
        def debug_callback(msg):
            debug_messages.append(msg)
            debug_text.text("\n".join(debug_messages[-5:]))  # Show last 5 messages
        
        travel_map, markers_added, total_activities, failed_locations = create_map_with_route(
            destination, travel_plan, map_status, progress_bar, debug_callback
        )
        
        progress_bar.empty()
        debug_text.empty()
        map_status.empty()  # Clear the loading message
        
        if travel_map:
            # Show marker success rate
            if markers_added < total_activities:
                st.warning(f"⚠️ {markers_added} out of {total_activities} locations found. Some activities couldn't be mapped.")
                if failed_locations:
                    with st.expander("❌ Failed locations (click to see)"):
                        for loc in failed_locations:
                            st.text(f"• {loc}")
            else:
                st.success(f"✅ All {markers_added} locations successfully mapped!")
            
            st_folium(travel_map, width=700, height=600, returned_objects=[])
        else:
            st.warning("Could not create map. Some locations may not have been found.")
            
        st.info("💡 Tip: Click on the markers to see details about each location!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Made with ❤️ for family adventures | Powered by Google Gemini & Streamlit</p>
</div>
""", unsafe_allow_html=True)

