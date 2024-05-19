// src/app/page.js
"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import axios from "axios";
import styles from "./page.module.css";

export default function Home() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState("");
  const [tripType, setTripType] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [dailyPlan, setDailyPlan] = useState("");
  const [images, setImages] = useState([]);
  const [step, setStep] = useState(1); // 1: form, 2: suggestions, 3: plan
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [loading, setLoading] = useState(false); // New state for loading
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleSubmit = async (event) => {
    event.preventDefault();
    const queryParams = { startDate, endDate, budget, tripType };
    const query = new URLSearchParams(queryParams).toString();
    router.push(`/?${query}`);
    setStep(2);
    fetchSuggestions(queryParams);
  };

  const fetchSuggestions = async (queryParams) => {
    setLoading(true); // Set loading state to true when fetching starts
    try {
      const response = await axios.post("http://127.0.0.1:8000/get-travel-suggestions/", {
        start_date: queryParams.startDate,
        end_date: queryParams.endDate,
        budget: parseInt(queryParams.budget),
        trip_type: queryParams.tripType,
      });

      const destinations = response.data;
      const updatedDestinations = await Promise.all(
        destinations.map(async (destination) => {
          const flightInfo = await getCheapestFlight(destination, queryParams.startDate, queryParams.endDate);
          const hotelInfo = await getMostExpensiveAffordableHotel(destination, queryParams.startDate, queryParams.endDate, flightInfo.remainingBudget);
          return {
            ...destination,
            flightPrice: flightInfo.price,
            hotelPrice: hotelInfo.price,
            totalPrice: flightInfo.price + hotelInfo.price,
          };
        })
      );

      setSuggestions(updatedDestinations);
    } catch (error) {
      console.error("Error fetching suggestions:", error);
    } finally {
      setLoading(false); // Set loading state to false after fetching completes
    }
  };

  const getCheapestFlight = async (destination, startDate, endDate) => {
    // Mock flight information for demonstration
    return {
      price: 500, // Mocked price
      remainingBudget: budget - 500,
    };
  };

  const getMostExpensiveAffordableHotel = async (destination, startDate, endDate, remainingBudget) => {
    // Mock hotel information for demonstration
    return {
      price: 300, // Mocked price
    };
  };

  const handleSelect = (destination) => {
    setSelectedDestination(destination);
    setStep(3);
    fetchDailyPlan({ destination, startDate, endDate });
  };

  const fetchDailyPlan = async ({ destination, startDate, endDate }) => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/generate-daily-plan/", {
        destination,
        start_date: startDate,
        end_date: endDate,
      });
      setDailyPlan(response.data.daily_plan);
      setImages(response.data.images);
    } catch (error) {
      console.error("Error generating daily plan:", error);
    }
  };

  useEffect(() => {
    const queryParams = {
      startDate: searchParams.get("startDate"),
      endDate: searchParams.get("endDate"),
      budget: searchParams.get("budget"),
      tripType: searchParams.get("tripType"),
    };
    if (queryParams.startDate && queryParams.endDate && queryParams.budget && queryParams.tripType) {
      fetchSuggestions(queryParams);
    }
  }, [searchParams]);

  return (
    <main className={styles.main}>
      {step === 1 && (
        <div className={styles.formContainer}>
          <h1 className="text-2xl font-bold text-center">Trip Planner</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className={styles.formLabel}>Start Date:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className={styles.formInput}
              />
            </div>
            <div>
              <label className={styles.formLabel}>End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                className={styles.formInput}
              />
            </div>
            <div>
              <label className={styles.formLabel}>Budget (USD):</label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                required
                className={styles.formInput}
              />
            </div>
            <div>
              <label className={styles.formLabel}>Trip Type:</label>
              <select
                value={tripType}
                onChange={(e) => setTripType(e.target.value)}
                required
                className={styles.formInput}
              >
                <option value="">Select</option>
                <option value="beach">Beach</option>
                <option value="city">City</option>
                <option value="ski">Ski</option>
              </select>
            </div>
            <button type="submit" className={styles.formButton}>
              Get Suggestions
            </button>
          </form>
        </div>
      )}

      {step === 2 && (
        <div className="w-full max-w-4xl p-8 space-y-6 bg-white rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-center">Suggested Destinations</h1>
          {loading ? (
            <p className="text-center">Loading...</p>
          ) : (
            <ul className={styles.suggestionsList}>
              {suggestions.map((suggestion, index) => (
                <li key={index} className={styles.suggestionItem}>
                  <h2 className={styles.suggestionTitle}>{suggestion.destination}</h2>
                  <p className="text-sm text-gray-600">Total Price: ${suggestion.totalPrice}</p>
                  <p className={styles.suggestionSummary}>{suggestion.summary}</p>
                  <button
                    onClick={() => handleSelect(suggestion.destination)}
                    className={styles.suggestionButton}
                  >
                    Select
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {step === 3 && (
        <div className={styles.dailyPlanContainer}>
          <h1 className="text-2xl font-bold text-center">Daily Plan for {selectedDestination}</h1>
          <div className={styles.dailyPlanText}>
            {dailyPlan.split("\n").map((line, index) => (
              <p key={index}>{line}</p>
            ))}
          </div>
          <h2 className="text-xl font-semibold">Images</h2>
          {images.length === 0 ? (
            <p className="text-center">Loading...</p>
          ) : (
            <div className={styles.imagesContainer}>
              {images.map((image, index) => (
                <img key={index} src={image} alt={`Image ${index + 1}`} className={styles.dailyPlanImage} />
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
