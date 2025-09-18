import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';

const ExoplanetsTab = () => {
  const [data, setData] = useState([]);
  const [yearFilter, setYearFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchExoplanets = async (year) => {
    setLoading(true);
    setError(null);
    try {
      let url = '/api/exoplanets/search?';
      if (year) {
        url += `discovery_year=${year}`;
      }
      const response = await axios.get(url);
      setData(response.data.data);
    } catch (err) {
      setError('Failed to fetch exoplanets data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExoplanets(yearFilter);
  }, [yearFilter]);

  // Prepare data for timeline chart (discovery per year)
  const discoveryCounts = data.reduce((acc, planet) => {
    const year = planet.disc_year || 'Unknown';
    acc[year] = (acc[year] || 0) + 1;
    return acc;
  }, {});

  const years = Object.keys(discoveryCounts).sort();
  const counts = years.map((y) => discoveryCounts[y]);

  return (
    <div>
      <h3>Exoplanets Discovery Timeline</h3>
      <div className="mb-3">
        <label htmlFor="yearFilter" className="form-label">
          Filter by Discovery Year:
        </label>
        <input
          type="number"
          id="yearFilter"
          className="form-control"
          placeholder="e.g. 2020"
          value={yearFilter}
          onChange={(e) => setYearFilter(e.target.value)}
        />
      </div>
      {loading && <p>Loading data...</p>}
      {error && <p className="text-danger">{error}</p>}
      {!loading && !error && data.length > 0 && (
        <Plot
          data={[
            {
              x: years,
              y: counts,
              type: 'bar',
              marker: { color: 'rgb(0,123,255)' },
            },
          ]}
          layout={{
            width: 700,
            height: 400,
            title: 'Number of Exoplanets Discovered per Year',
            xaxis: { title: 'Year' },
            yaxis: { title: 'Count' },
          }}
        />
      )}
      {!loading && !error && data.length === 0 && <p>No data found.</p>}
    </div>
  );
};

export default ExoplanetsTab;
