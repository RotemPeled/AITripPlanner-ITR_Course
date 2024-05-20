"use client";
import { useState, useEffect } from 'react';
import styles from './page.module.css';  // Import the CSS module

function HomePage() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [budget, setBudget] = useState('');
  const [tripType, setTripType] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedDestination, setSelectedDestination] = useState('');
  const [selectedFlightPrice, setSelectedFlightPrice] = useState(null);
  const [selectedHotelPrice, setSelectedHotelPrice] = useState(null);
  const [dailyPlan, setDailyPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  // State for form validation errors
  const [startDateError, setStartDateError] = useState('');
  const [endDateError, setEndDateError] = useState('');
  const [budgetError, setBudgetError] = useState('');
  const [tripTypeError, setTripTypeError] = useState('');

  const validateStartDate = (date) => {
    const selectedDate = new Date(date);
    const today = new Date();
    if (selectedDate < today) {
      setStartDateError('Start date has expired');
    } else {
      setStartDateError('');
    }
  };

  const validateEndDate = (start, end) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    if (endDate < startDate) {
      setEndDateError('End date cannot be before start date');
    } else {
      setEndDateError('');
    }
  };

  const validateBudget = (amount) => {
    if (amount <= 0) {
      setBudgetError('Budget must be greater than 0');
    } else {
      setBudgetError('');
    }
  };

  const validateTripType = (type) => {
    if (!type) {
      setTripTypeError('Please select a trip type');
    } else {
      setTripTypeError('');
    }
  };

  // useEffect hooks to validate on change
  useEffect(() => {
    if (startDate) validateStartDate(startDate);
    if (endDate) validateEndDate(startDate, endDate);
    if (budget) validateBudget(budget);
    if (tripType) validateTripType(tripType);
  }, [startDate, endDate, budget, tripType]);

  const handleSearch = async () => {
    if (!startDate) setStartDateError('Please select a start date');
    if (!endDate) setEndDateError('Please select an end date');
    if (!budget) setBudgetError('Please enter a budget');
    if (!tripType) setTripTypeError('Please select a trip type');

    if (!startDateError && !endDateError && !budgetError && !tripTypeError && startDate && endDate && budget && tripType) {
      setLoading(true);
      const response = await fetch('http://localhost:8000/get-travel-suggestions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
          budget: budget,
          trip_type: tripType
        })
      });
      const data = await response.json();
      setSuggestions(data);
      setLoading(false);
    }
  };

  const handleSelectDestination = async (suggestion) => {
    setLoading(true);
    setSelectedDestination(suggestion.destination);
    setSelectedFlightPrice(suggestion.flight_price);  // Store the flight price when a destination is selected
    setSelectedHotelPrice(suggestion.hotel_price);    // Store the hotel price when a destination is selected
    const response = await fetch('http://localhost:8000/generate-daily-plan/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        destination: suggestion.destination,
        start_date: startDate,
        end_date: endDate
      })
    });
    const data = await response.json();
    setDailyPlan(data);
    setLoading(false);
  };

  return (
    <div className={styles.pageContainer}>
      <style jsx global>{`
        html, body {
          height: 100%;
          margin: 0;
          padding: 0;
          background-color: #f0f0f0; /* Light gray background for the entire viewport */
          font-family: 'Arial', sans-serif;
        }

        * {
          box-sizing: border-box;
        }
      `}</style>
      {!selectedDestination && !suggestions.length && (
        <div className={styles.inputContainer}>
          <h1 className={styles.title}>Plan Your Trip</h1>
          <div className={styles.inputWrapper}>
            <input className={styles.inputField} type="date" value={startDate} onChange={e => setStartDate(e.target.value)} placeholder="Start Date" />
            {startDateError && <span className={styles.errorMessage}>{startDateError}</span>}
          </div>
          <div className={styles.inputWrapper}>
            <input className={styles.inputField} type="date" value={endDate} onChange={e => setEndDate(e.target.value)} placeholder="End Date" />
            {endDateError && <span className={styles.errorMessage}>{endDateError}</span>}
          </div>
          <div className={styles.inputWrapper}>
            <input className={`${styles.inputField} ${styles.noSpin}`} type="number" value={budget} onChange={e => setBudget(e.target.value)} placeholder="Budget in USD" />
            {budgetError && <span className={styles.errorMessage}>{budgetError}</span>}
          </div>
          <div className={styles.inputWrapper}>
            <select className={styles.inputField} value={tripType} onChange={e => setTripType(e.target.value)}>
              <option value="">Select Trip Type</option>
              <option value="ski">Ski</option>
              <option value="beach">Beach</option>
              <option value="city">City</option>
            </select>
            {tripTypeError && <span className={styles.errorMessage}>{tripTypeError}</span>}
          </div>
          <button className={styles.actionButton} onClick={handleSearch} disabled={loading || startDateError || endDateError || budgetError || tripTypeError}>Find Destinations</button>
        </div>
      )}

      {loading && <p className={styles.loadingMessage}>Loading...</p>}

      {!selectedDestination && suggestions.length > 0 && (
        <div>
          <h2 className={styles.title}>Suggested Destinations</h2>
          <ul className={styles.destinationsList}>
            {suggestions.map((suggestion, index) => (
              <li key={index} className={styles.destinationItem}>
                <h3 className={styles.destinationHeader}>{suggestion.destination}</h3>
                <p className={styles.destinationSummary}>Total Cost: ${suggestion.total_price}</p>
                <p className={styles.destinationSummary}>Summary: {suggestion.summary}</p>
                <button className={styles.actionButton} onClick={() => handleSelectDestination(suggestion)}>Select This Destination</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {selectedDestination && dailyPlan && (
        <div>
          <h2 className={styles.title}>Your Trip to {selectedDestination}</h2>
          <div className={styles.priceContainer}>
            <div className={styles.priceBox}>Flight Price: ${selectedFlightPrice}</div>
            <div className={styles.priceBox}>Hotel Price: ${selectedHotelPrice}</div>
            <div className={styles.priceBox}>Total Price: ${parseInt(selectedFlightPrice) + parseInt(selectedHotelPrice)}</div>
          </div>
          <div className={styles.dailyPlanContainer}>
            {dailyPlan.daily_plan.split('\n\n').map((day, index) => (
              <div key={index} className={styles.dailyPlanDay}>
                {day.split('\n').map((line, lineIndex) => (
                  <p key={lineIndex}>{line}</p>
                ))}
              </div>
            ))}
          </div>
          <div className={styles.dailyPlanImagesContainer}>
            {dailyPlan.images.map((image, index) => (
              image ? <img key={index} src={image} alt={`Visual representation ${index + 1}`} className={styles.dailyPlanImage} /> : <p key={index}>Image loading failed</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default HomePage;
