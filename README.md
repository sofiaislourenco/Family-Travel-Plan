# ✈️ Family Travel Planner

A beautiful and interactive web application to help you plan the perfect family vacation! Get AI-powered activity recommendations and visualize your trip on an interactive map.

## Features

- 🗺️ **Interactive Map**: See all your destinations pinned on a map with different colors for each day
- 🤖 **AI-Powered Recommendations**: Get personalized activity suggestions using Google Gemini AI
- 🖼️ **Real Location Photos**: Each activity shows actual photos from Google Places API
- 👨‍👩‍👧‍👦 **Family-Friendly**: Specify if you're traveling with kids and their ages for age-appropriate activities
- 🎯 **Kids Challenges**: Fun scavenger hunts and challenges for kids at each activity when traveling with children
- 📅 **Multi-Day Planning**: Plan trips from 1 to 30 days
- 📍 **Detailed Itinerary**: Get day-by-day breakdown with activity descriptions, durations, and locations

## Prerequisites

- Python 3.7 or higher
- **Google Gemini API key** (required - get one at https://aistudio.google.com/app/apikey)
- **Google Maps API key** (required - get one at https://console.cloud.google.com/apis/credentials)
  - Enable both "Places API" and "Maps JavaScript API" for your key

## Installation

1. **Activate your virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys** (create a `.env` file):
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```
   
   **Important**: Make sure to enable these APIs in Google Cloud Console:
   - Places API (for location photos and geocoding)
   - Maps JavaScript API (for map display)

## Usage

1. **Run the application**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser**: The app will automatically open at `http://localhost:8501`

3. **Enter your trip details**:
   - Destination (e.g., "Paris, France")
   - Number of days
   - Whether you're traveling with kids and their ages

4. **Generate your plan**: Click the "Generate Travel Plan" button

5. **Explore your itinerary**:
   - View the detailed day-by-day itinerary on the left with real photos from Google Places
   - Interact with the map on the right to see all locations
   - Click on map markers to see activity details

## How It Works

1. **Input Collection**: The app collects your destination, trip duration, and family information
2. **AI Generation**: Uses Google Gemini AI to generate personalized activity recommendations
3. **Kids Challenges**: If traveling with kids, automatically generates fun challenges and scavenger hunts for each activity
4. **Geocoding**: Converts location names to coordinates using Geopy
5. **Map Visualization**: Creates an interactive map with Folium showing all activities (including challenges in popups!)
6. **Display**: Presents the itinerary and map in an easy-to-use interface

## Technologies Used

- **Streamlit**: Web application framework
- **Google Gemini AI**: AI-powered activity recommendations
- **Google Places API**: Real photos of actual locations
- **Google Maps**: Interactive map visualization
- **Folium**: Map rendering library
- **Geopy**: Location geocoding
- **streamlit-folium**: Integration between Streamlit and Folium

## Tips

- Be specific with your destination (include city and country)
- The more accurate the destination, the better the location pins
- API keys are stored securely in the .env file
- Map generation takes 15-30 seconds due to geocoding rate limits
- Try different age groups for varied activity recommendations

## Example Destinations

- Paris, France
- Tokyo, Japan
- New York City, USA
- Barcelona, Spain
- London, UK
- Sydney, Australia

## Troubleshooting

- **Location not found**: Try being more specific with the destination name
- **API errors**: Check that your Gemini API key is valid (get one at https://aistudio.google.com/app/apikey)
- **Map not loading**: Ensure you have an internet connection

## Future Enhancements

- Save and export itineraries
- Budget estimation for activities
- Restaurant recommendations
- Hotel suggestions
- Weather information
- Offline map support

## License

This project is created for personal use. Feel free to modify and enhance!

---

Made with ❤️ for family adventures

