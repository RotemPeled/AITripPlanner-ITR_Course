import datetime
import re
from openai import OpenAI
from serpapi import GoogleSearch
import requests


def get_travel_suggestions(start_date, end_date, budget, trip_type):
    api_key = 'sk-proj-SRGCSAzogrcsQIu2kwiZT3BlbkFJp02fsLG6iUdA7G5kEfKg'
    client = OpenAI(api_key=api_key)
    
    month = start_date.strftime("%B")    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a travel advisor."},
            {"role": "user", "content": f"Given a budget of ${budget} for a {trip_type} trip in the month of {month}, suggest 5 destinations worldwide. Please provide the response in the following format:\n1. Destination, Country (Airport Code) - Description\n2. Destination, Country (Airport Code) - Description\n3. Destination, Country (Airport Code) - Description\n4. Destination, Country (Airport Code) - Description\n5. Destination, Country (Airport Code) - Description"}
        ]    
    )

    print("Here are some suggested destinations for your trip:")
    suggestions = completion.choices[0].message.content
    print(suggestions)
    
    destinations = parse_destinations(suggestions)
    return destinations

def parse_destinations(suggestions):
    # Use regex to find all the destinations, each starting with a number and followed by a dash
    pattern = r'\d+\.\s*(.*?), (.*?) \((.*?)\) -'
    matches = re.findall(pattern, suggestions)
    return [{"city": match[0], "country": match[1], "airport_code": match[2]} for match in matches]

def get_cheapest_flight(origin, destination, start_date, end_date):
    destination_airport_code = destination["airport_code"]
    params = {
        "engine": "google_flights",
        "departure_id": "TLV",
        "arrival_id": destination_airport_code,
        "outbound_date": start_date.strftime("%Y-%m-%d"),
        "return_date": end_date.strftime("%Y-%m-%d"),
        "currency": "USD",
        "api_key": "0d242c51ae7e9dc9fcf75cebea6130731f580d5e2739bc47b4f6b38812183c52"
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        
        if response.status_code == 200:
            data = response.json()
            price_insights = data.get("price_insights", {})
            if price_insights:
                lowest_price = price_insights.get("lowest_price")
                if lowest_price is not None:
                    return {"destination": f"{destination['city']}, {destination['country']}", "price": lowest_price}
                else:
                    return {"city": destination['city'], "country": destination['country'], "price": None}
            else:
                return {"city": destination['city'], "country": destination['country'], "price": None}
        else:
            print(f"Failed to fetch from SerpAPI. Status code: {response.status_code}, Response body: {response.text}")
            return {"city": destination['city'], "country": destination['country'], "price": None}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"city": destination['city'], "country": destination['country'], "price": None}


def search_flights(destinations, start_date, end_date):
    results = []
    for destination in destinations:
        flight = get_cheapest_flight("Tel Aviv", destination, start_date, end_date)
        if flight['price']:
            results.append(f"{flight['destination']}: ${flight['price']}")
        else:
            results.append(f"No flights found for {flight['city']}, {flight['country']}.")
    
    for result in results:
        print(result)

def validate_date(prompt_message):
    while True:
        date_input = input(prompt_message)
        try:
            valid_date = datetime.datetime.strptime(date_input, "%Y-%m-%d")
            if valid_date < datetime.datetime.now():
                print("Please enter a future date.")
            else:
                return valid_date
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

def validate_budget(prompt_message):
    while True:
        budget_input = input(prompt_message)
        try:
            budget = int(budget_input)
            if budget > 0:
                return budget
            else:
                print("Please enter a positive number for the budget.")
        except ValueError:
            print("Invalid budget. Please enter a numeric value.")

def validate_trip_type(prompt_message):
    valid_types = ["ski", "beach", "city"]
    while True:
        trip_type = input(prompt_message).lower()
        if trip_type in valid_types:
            return trip_type
        else:
            print(f"Invalid trip type. Please choose from {', '.join(valid_types)}.")

def main():
    print("Welcome to the Trip Planner!")
    while True:
        start_date = validate_date("Enter the start date of your trip (YYYY-MM-DD): ")
        end_date = validate_date("Enter the end date of your trip (YYYY-MM-DD): ")
        if end_date <= start_date:
            print("End date must be after start date. Please enter the dates again.")
            continue
        else:
            break
    
    budget = validate_budget("Enter your total budget for the trip in USD: ")
    trip_type = validate_trip_type("Enter the type of your trip (ski, beach, city): ")
    
    destinations = get_travel_suggestions(start_date, end_date, budget, trip_type)
    search_flights(destinations, start_date, end_date)

if __name__ == "__main__":
    main()
