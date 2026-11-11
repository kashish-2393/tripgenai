
import os
import json
import time
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def clean_json_response(text):
    """Clean Gemini's response and convert it into JSON."""

    result = text.strip()

    if result.startswith("```"):
        result = re.sub(r"^```(?:json)?\s*", "", result)
        result = re.sub(r"\s*```$", "", result)

    # Extract JSON if extra text is present
    if not result.startswith("{"):
        start = result.find("{")
        end = result.rfind("}")

        if start != -1 and end != -1:
            result = result[start:end + 1]

    return json.loads(result)


def generate_fallback_itinerary(trip_details):
    """
    Generate a local backup itinerary if Gemini is unavailable.
    This does not require an API connection.
    """

    destination = trip_details.get("destination", "Your Destination")
    origin = trip_details.get("origin", "Your Starting Location")

    try:
        duration = int(trip_details.get("duration", 3))
        duration = max(1, min(duration, 14))
    except (ValueError, TypeError):
        duration = 3

    try:
        budget = float(trip_details.get("budget", 10000))
    except (ValueError, TypeError):
        budget = 10000

    budget = max(0, budget)

    accommodation = budget * 0.35
    food = budget * 0.25
    transport = budget * 0.20
    activities = budget * 0.15
    miscellaneous = budget * 0.05

    def rupees(amount):
        return f"₹{amount:,.0f}"

    days = []

    for day_number in range(1, duration + 1):

        days.append({
            "day": day_number,
            "title": f"Explore {destination} - Day {day_number}",

            "morning": (
                f"Start your day with breakfast and explore "
                f"popular attractions in {destination}."
            ),

            "afternoon": (
                f"Enjoy local sightseeing, visit nearby landmarks "
                f"and explore the local culture of {destination}."
            ),

            "evening": (
                f"Explore a local market, enjoy regional food "
                f"and relax in {destination}."
            ),

            "places": [
                f"Popular attractions in {destination}",
                f"Local market in {destination}"
            ]
        })

    return {
        "destination": destination,

        "summary": (
            f"Here is a backup {duration}-day travel plan for "
            f"{destination}, starting from {origin}. "
            "This sample itinerary was generated locally because "
            "the AI service is temporarily unavailable. "
            "Please verify attractions, prices and travel details."
        ),

        "days": days,

        "hotel_suggestions": [
            {
                "name": f"Budget hotels in {destination}",
                "category": "Budget",
                "estimated_price": "Estimated ₹1,000–₹2,000 per night",
                "reason": "A budget-friendly accommodation search option."
            },
            {
                "name": f"Mid-range hotels in {destination}",
                "category": "Mid-range",
                "estimated_price": "Estimated ₹2,000–₹4,000 per night",
                "reason": "An option for travellers seeking additional comfort."
            }
        ],

        "food_suggestions": [
            {
                "name": f"Local restaurants in {destination}",
                "cuisine": "Local cuisine",
                "estimated_cost": "Estimated ₹200–₹500",
                "reason": "Explore local restaurants and regional dishes."
            },
            {
                "name": f"Popular food places in {destination}",
                "cuisine": "Regional and Indian food",
                "estimated_cost": "Estimated ₹150–₹400",
                "reason": "Explore different local food options."
            }
        ],

        "popular_dishes": [
            f"Popular local dishes of {destination}",
            "Regional Indian specialities"
        ],

        "daily_food_budget": rupees(food / duration),

        "budget_breakdown": {
            "accommodation": rupees(accommodation),
            "food": rupees(food),
            "transport": rupees(transport),
            "activities": rupees(activities),
            "miscellaneous": rupees(miscellaneous),
            "total": rupees(budget)
        },

        "tips": [
            f"Check weather conditions before travelling to {destination}.",
            "Verify hotel prices and availability before booking.",
            "Keep some extra money for unexpected expenses.",
            "Check local transport options before starting your journey."
        ],

        "fallback_mode": True
    }


def generate_itinerary(trip_details):

    # Models previously tested successfully
    models = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite"
    ]

    interests = trip_details.get("interests", [])

    if isinstance(interests, str):
        interests = [interests]

    interests_text = ", ".join(interests) if interests else "General sightseeing"

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
    Interests: {interests_text}
    Food preference: {trip_details['food_preference']}

    Return ONLY valid JSON in this structure:

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
          "reason": "Why this hotel is suitable"
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

    Instructions:
    1. Generate exactly {trip_details['duration']} itinerary days.
    2. Respect the traveller's total budget.
    3. Consider travel style and interests.
    4. Follow the selected food preference.
    5. Recommend local food and popular dishes.
    6. Provide estimated prices in INR.
    7. Do not claim hotel availability is verified.
    8. Label hotel and restaurant recommendations as suggestions.
    9. Return valid JSON only.
    """

    # Try Gemini models with automatic retry
    if client:

        for model in models:

            for attempt in range(2):

                try:
                    print(f"Trying model: {model}, attempt: {attempt + 1}")

                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )

                    if not response.text:
                        raise ValueError("Empty response from Gemini.")

                    itinerary = clean_json_response(response.text)

                    itinerary["fallback_mode"] = False

                    print(f"Successfully generated itinerary using {model}")

                    return itinerary

                except Exception as error:

                    print(f"Gemini error with {model}: {error}")

                    if attempt == 0:
                        time.sleep(2)

    # If API key is missing or all Gemini attempts fail
    print("Gemini unavailable. Using local fallback itinerary.")

    return generate_fallback_itinerary(trip_details)
