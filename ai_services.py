import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def generate_itinerary(trip_details):

    if not client:
        raise Exception("Gemini API key is missing. Check your .env file.")

    prompt = f"""
    You are TripGenie AI, a professional travel planner.

    Create a personalised travel plan using these details:

    Starting location: {trip_details['origin']}
    Destination: {trip_details['destination']}
    Start date: {trip_details['start_date']}
    End date: {trip_details['end_date']}
    Duration: {trip_details['duration']} days
    Total budget: ₹{trip_details['budget']}
    Travellers: {trip_details['travellers']}
    Travel style: {trip_details['travel_style']}
    Interests: {', '.join(trip_details['interests'])}
    Food preference: {trip_details['food_preference']}

    Return ONLY valid JSON in this exact structure:

    {{
      "destination": "Destination name",
      "summary": "Short trip summary",

      "days": [
        {{
          "day": 1,
          "title": "Day title",
          "morning": "Morning activities",
          "afternoon": "Afternoon activities",
          "evening": "Evening activities",
          "places": ["Place 1", "Place 2"]
        }}
      ],

      "hotel_suggestions": [
        {{
          "name": "Hotel suggestion",
          "category": "Budget / Mid-range / Luxury",
          "estimated_price": "Estimated price per night in INR",
          "reason": "Why this hotel type is suitable"
        }}
      ],

      "food_suggestions": [
        {{
          "name": "Food or restaurant suggestion",
          "cuisine": "Cuisine type",
          "estimated_cost": "Estimated cost in INR",
          "reason": "Why it is worth trying"
        }}
      ],

      "popular_dishes": [
        "Local dish 1",
        "Local dish 2"
      ],

      "daily_food_budget": "Estimated daily food budget in INR",

      "budget_breakdown": {{
        "accommodation": "Estimated amount",
        "food": "Estimated amount",
        "transport": "Estimated amount",
        "activities": "Estimated amount",
        "miscellaneous": "Estimated amount",
        "total": "Estimated total"
      }},

      "tips": [
        "Travel tip 1",
        "Travel tip 2"
      ]
    }}

    Important instructions:

    1. Generate exactly {trip_details['duration']} itinerary days.
    2. Respect the traveller's total budget.
    3. Consider their travel style and interests.
    4. Follow the selected food preference.
    5. Recommend local food and famous dishes.
    6. Provide realistic estimated prices in INR.
    7. Do not claim that suggested hotels have verified availability.
    8. AI hotel and restaurant suggestions must be labelled as suggestions,
       not verified business listings.
    9. Return valid JSON only. Do not use Markdown code fences.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    result = response.text.strip()

    if result.startswith("```"):
        result = result.split("\n", 1)[1]
        result = result.rsplit("```", 1)[0].strip()

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise Exception("Gemini returned an invalid response. Please try again.")
