import React, { useState, useEffect } from 'react';
import axios from 'axios';

const IssTab = () => {
  const [position, setPosition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchIssPosition = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/iss/');
      setPosition(response.data);
    } catch (err) {
      setError('Failed to fetch ISS position');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssPosition();
    const interval = setInterval(fetchIssPosition, 5000); // refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h3>ISS Current Location</h3>
      {loading && <p>Loading ISS position...</p>}
      {error && <p className="text-danger">{error}</p>}
      {position && (
        <div>
          <p>Latitude: {position.latitude.toFixed(2)}</p>
          <p>Longitude: {position.longitude.toFixed(2)}</p>
          <p>Altitude: {position.altitude.toFixed(2)} km</p>
          <p>Velocity: {position.velocity.toFixed(2)} km/h</p>
          <p>Timestamp: {new Date(position.timestamp * 1000).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
};

export default IssTab;
