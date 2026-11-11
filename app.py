from flask import Flask, render_template, request
from datetime import datetime
from dotenv import load_dotenv

from ai_services import generate_itinerary


load_dotenv()

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/planner")
def planner():
    return render_template("index.html")


@app.route("/generate-trip", methods=["POST"])
def generate_trip():

    origin = request.form.get("origin", "").strip()
    destination = request.form.get("destination", "").strip()

    start_date = request.form.get("start_date", "")
    end_date = request.form.get("end_date", "")

    budget = request.form.get("budget", "")
    travellers = request.form.get("travellers", "1")

    travel_style = request.form.get("travel_style", "Balanced")

    interests = request.form.getlist("interests")

    food_preference = request.form.get(
        "food_preference", "Any"
    )

    # Validate required fields.

    if not all([
        origin,
        destination,
        start_date,
        end_date,
        budget
    ]):

        return "Please fill in all required fields.", 400

    try:

        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        budget = float(budget)
        travellers = int(travellers)

        duration = (end - start).days + 1

        if duration < 1 or duration > 14:
            return "Trip duration must be between 1 and 14 days.", 400

        if budget <= 0 or travellers <= 0:
            return "Budget and travellers must be positive.", 400

    except ValueError:

        return "Please enter valid dates, budget and traveller details.", 400

    trip_details = {

        "origin": origin,
        "destination": destination,

        "start_date": start_date,
        "end_date": end_date,

        "duration": duration,

        "budget": budget,
        "travellers": travellers,

        "travel_style": travel_style,
        "interests": interests,

        "food_preference": food_preference
    }

    itinerary = None
    ai_error = None

    # Generate AI itinerary and suggestions.

    try:

        itinerary = generate_itinerary(trip_details)

    except Exception as e:

        ai_error = str(e)

    # Find real hotels and restaurants through OpenStreetMap.

    

    return render_template(

        "results.html",

        trip_details=trip_details,

        itinerary=itinerary,

        ai_error=ai_error,

        
    )


if __name__ == "__main__":

    app.run(debug=True)