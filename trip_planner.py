import datetime
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import requests

app = FastAPI()

# Add CORS middleware to allow requests from your Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize your API key at the start of your script
api_key = 'sk-proj-SRGCSAzogrcsQIu2kwiZT3BlbkFJp02fsLG6iUdA7G5kEfKg'
client = OpenAI(api_key=api_key)

class TripRequest(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    budget: int
    trip_type: str

class Destination(BaseModel):
    city: str
    country: str
    airport_code: str
    summary: str

class TripSuggestion(BaseModel):
    destination: str
    total_price: Optional[int]
    summary: str

class DailyPlanRequest(BaseModel):
    destination: str
    start_date: datetime.date
    end_date: datetime.date

class DailyPlanResponse(BaseModel):
    daily_plan: str
    images: List[str]

def get_travel_suggestions(start_date, end_date, budget, trip_type):    
    month = start_date.strftime("%B")    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel advisor."},
                {"role": "user", "content": f"Given a budget of ${budget} for a {trip_type} trip in the month of {month}, suggest 5 destinations worldwide. Please provide the response in the following format:\n1. Destination, Country (Airport Code) - Description\n2. Destination, Country (Airport Code) - Description\n3. Destination, Country (Airport Code) - Description\n4. Destination, Country (Airport Code) - Description\n5. Destination, Country (Airport Code) - Description"}
            ]    
        )
        suggestions = completion.choices[0].message.content    
        destinations = parse_destinations(suggestions)
        return destinations
    except Exception as e:
        print(f"Failed to fetch travel suggestions. Error: {str(e)}")
        return []

def parse_destinations(suggestions):
    pattern = r'\d+\.\s*(.*?), (.*?) \((.*?)\) - (.*)'
    matches = re.findall(pattern, suggestions)
    return [
        {
            "city": match[0], 
            "country": match[1], 
            "airport_code": match[2].split('/')[0],  # Takes the first airport code if multiple are provided
            "summary": match[3]
        } for match in matches
    ]

# Mock function to replace actual API call
def get_cheapest_flight(origin, destination, start_date, end_date):
    return {
        "destination": f"{destination['city']}, {destination['country']}",
        "price": 500  # Mocked price
    }

# Mock function to replace actual API call
def get_most_expensive_affordable_hotel(city, country, budget, start_date, end_date):
    return {
        "name": "Mock Hotel",
        "price": 300  # Mocked price
    }

def search_flights_and_hotels(destinations, start_date, end_date, budget):
    flight_and_hotel_results = []
    for destination in destinations:
        flight_info = get_cheapest_flight("Tel Aviv", destination, start_date, end_date)
        if flight_info['price']:
            remaining_budget = budget - flight_info['price']
            hotel_info = get_most_expensive_affordable_hotel(destination['city'], destination['country'], remaining_budget, start_date, end_date)
            if 'name' in hotel_info and 'price' in hotel_info:
                total_price = flight_info['price'] + hotel_info['price']
                flight_and_hotel_results.append({
                    "destination": f"{flight_info['destination']}",
                    "flight_price": flight_info['price'],
                    "hotel_price": hotel_info['price'],
                    "total_price": total_price,
                    "summary": destination['summary']
                })            
            else:
                flight_and_hotel_results.append({
                    "destination": f"{flight_info['destination']}",
                    "flight_price": flight_info['price'],
                    "hotel_price": None,
                    "total_price": None,
                    "hotel_error": hotel_info.get('error', 'Hotel not found within budget'),
                    "summary": destination['summary']
                })
        else:
            flight_and_hotel_results.append({
                "destination": f"{destination['city']}, {destination['country']}",
                "flight_price": None,
                "hotel_price": None,
                "total_price": None,
                "flight_error": f"No flights found for {destination['city']}, {destination['country']}",
                "summary": destination['summary']
            })
    return flight_and_hotel_results

def generate_daily_plan(destination, start_date, end_date):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a travel guide and a creative advisor for visual content."},
            {"role": "user", "content": f"I am planning a trip to {destination} from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}. Please suggest a detailed daily itinerary. At the end provide exactly 4 descriptions that could visually summarize the entire trip. make the description clear and detailed. please use this format for the 4 descriptions: visually summarize: \n1. A picture of the Eiffel Tower at sunset, symbolizing the iconic landmark of Paris.\n2. A snapshot of colorful flowers in full bloom at the gardens of Versailles, representing the beauty of French landscapes.\n3. An image of the Seine River with historic bridges in the background, showcasing the romantic charm of Paris.\n4. A shot of street artists painting in Montmartre, capturing the artistic spirit and bohemian vibe of the neighborhood."}
        ]
    )

    # Full content of the response
    full_content = completion.choices[0].message.content

    # Use regex to split the content at "visually summarize:" (case-insensitive)
    parts = re.split(r'(?i)visually summarize:', full_content, 1)  # '(?i)' is a regex flag for case-insensitive matching
    if len(parts) > 1:
        plan_content = parts[0].strip()
        image_descriptions_content = parts[1].strip()
        image_descriptions = extract_image_descriptions("Visually summarize:" + image_descriptions_content)
    else:
        plan_content = full_content
        image_descriptions = []

    return plan_content, image_descriptions

def extract_image_descriptions(image_descriptions_content):
    descriptions = []
    lines = image_descriptions_content.split('\n')
    for line in lines:
        # Check if line starts with a number followed by a period which denotes the start of a description
        if line.strip().startswith(("1.", "2.", "3.", "4.")):
            description = line.split(". ", 1)[1] if ". " in line else line
            descriptions.append(description)
    return descriptions

def generate_images(descriptions):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    images = []
    for description in descriptions:
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json={
                "prompt": description,
                "n": 1,
                "size": "1024x1024"
            }
        )
        if response.status_code == 200:
            data = response.json()
            try:
                images.append(data['data'][0]['url'])
            except KeyError:
                print("No URL found in the response:", data)
                images.append(None)
        else:
            print(f"Failed to generate image with status code {response.status_code}: {response.text}")
            images.append(None)
    return images

@app.post("/get-travel-suggestions/", response_model=List[TripSuggestion])
def get_suggestions(request: TripRequest):
    destinations = get_travel_suggestions(request.start_date, request.end_date, request.budget, request.trip_type)
    flight_and_hotel_results = search_flights_and_hotels(destinations, request.start_date, request.end_date, request.budget)
    return [
        TripSuggestion(
            destination=result['destination'],
            total_price=result.get('total_price'),
            summary=result['summary']
        ) for result in flight_and_hotel_results
    ]

@app.post("/generate-daily-plan/", response_model=DailyPlanResponse)
def generate_plan(request: DailyPlanRequest):
    plan_content, image_descriptions = generate_daily_plan(request.destination, request.start_date, request.end_date)
    images = generate_images(image_descriptions)
    return DailyPlanResponse(
        daily_plan=plan_content,
        images=images
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
