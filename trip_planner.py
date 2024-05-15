import datetime
import re
from openai import OpenAI
from serpapi import GoogleSearch
import requests
import json


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

    suggestions = completion.choices[0].message.content    
    destinations = parse_destinations(suggestions)
    return destinations , suggestions

def parse_destinations(suggestions):
    pattern = r'\d+\.\s*(.*?), (.*?) \((.*?)\) -'
    matches = re.findall(pattern, suggestions)
    return [
        {
            "city": match[0], 
            "country": match[1], 
            "airport_code": match[2].split('/')[0]  # Takes the first airport code if multiple are provided
        } for match in matches
    ]


def get_cheapest_flight(origin, destination, start_date, end_date):
    destination_airport_code = destination["airport_code"]
    params = {
        "engine": "google_flights",
        "departure_id": "TLV",
        "arrival_id": destination_airport_code,
        "outbound_date": start_date.strftime("%Y-%m-%d"),
        "return_date": end_date.strftime("%Y-%m-%d"),
        "currency": "USD",
        "api_key": "40410806235e0f18253ef31c1d87e51aa12f7bb25cf0c6f9bc0bb946c4a02e8f"
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
    

def get_most_expensive_affordable_hotel(city, country, budget, start_date, end_date):
    params = {
        "engine": "google_hotels",
        "q": f"hotels in {city}, {country}",
        "check_in_date": start_date.strftime("%Y-%m-%d"),
        "check_out_date": end_date.strftime("%Y-%m-%d"),
        "currency": "USD",
        "sort_by": "3",  # sort by lowest price
        "api_key": "40410806235e0f18253ef31c1d87e51aa12f7bb25cf0c6f9bc0bb946c4a02e8f"
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)

        if response.status_code == 200:
            data = response.json()
            hotels = data.get("properties", [])
            most_expensive_affordable_hotel = None

            for hotel in hotels:
                price = hotel.get("total_rate", {}).get("extracted_lowest")
                if price and price <= budget:
                    if not most_expensive_affordable_hotel or price > most_expensive_affordable_hotel["price"]:
                        most_expensive_affordable_hotel = {
                            "name": hotel["name"],
                            "price": price,
                        }
                elif price and price > budget:
                    break  # Break out of the loop if price exceeds the budget

            if most_expensive_affordable_hotel:
                return most_expensive_affordable_hotel
            else:
                return {"error": "No affordable hotels found within the budget."}
        else:
            return {"error": f"Failed to fetch from SerpAPI. Status code: {response.status_code}, Response body: {response.text}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}
    
    
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
                                    "total_price": total_price
                })            
            else:
                flight_and_hotel_results.append({
                                    "destination": f"{flight_info['destination']}",
                                    "flight_price": flight_info['price'],
                                    "hotel_price": None,
                                    "total_price": None,
                                    "hotel_error": hotel_info['error']
                })
        else:
            flight_and_hotel_results.append({
                            "destination": f"{destination['city']}, {destination['country']}",
                            "flight_price": None,
                            "hotel_price": None,
                            "total_price": None,
                            "flight_error": f"No flights found for {destination['city']}, {destination['country']}"
            })
    return flight_and_hotel_results

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
    
    destinations, suggestions = get_travel_suggestions(start_date, end_date, budget, trip_type)

    flight_and_hotel_results = search_flights_and_hotels(destinations, start_date, end_date, budget)
    
    # Display the collected information
    print("Here are the options for your trip:")
    for index, result in enumerate(flight_and_hotel_results, start=1):
        print(f"{index}. Destination: {result['destination']}, Total Price: ${result['total_price'] if result['total_price'] else 'N/A'}")

    # Allow the user to choose a destination
    while True:
        choice = input("Please enter the number of the destination you choose: ")
        try:
            choice_index = int(choice)
            if 1 <= choice_index <= len(flight_and_hotel_results):
                chosen_destination = flight_and_hotel_results[choice_index - 1]
                print(f"Chosen Destination: {chosen_destination['destination']}, Total Price: ${chosen_destination['total_price'] if chosen_destination['total_price'] else 'N/A'}")
                break
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()
