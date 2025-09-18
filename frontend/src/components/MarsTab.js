import React, { useState, useEffect } from 'react';
import axios from 'axios';

const MarsTab = () => {
  const [photos, setPhotos] = useState([]);
  const [sol, setSol] = useState(1000);
  const [rover, setRover] = useState('curiosity');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMarsPhotos = async (solValue, roverName) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/mars/rover/${roverName}/photos?sol=${solValue}`);
      setPhotos(response.data.photos || []);
    } catch (err) {
      setError('Failed to fetch Mars photos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarsPhotos(sol, rover);
  }, [sol, rover]);

  return (
    <div>
      <h3>Mars Rover Photos</h3>
      <div className="mb-3">
        <label htmlFor="roverSelect" className="form-label">
          Select Rover:
        </label>
        <select
          id="roverSelect"
          className="form-select"
          value={rover}
          onChange={(e) => setRover(e.target.value)}
        >
          <option value="curiosity">Curiosity</option>
          <option value="perseverance">Perseverance</option>
          <option value="opportunity">Opportunity</option>
        </select>
      </div>
      <div className="mb-3">
        <label htmlFor="solInput" className="form-label">
          Martian Sol (Day):
        </label>
        <input
          type="number"
          id="solInput"
          className="form-control"
          value={sol}
          onChange={(e) => setSol(e.target.value)}
        />
      </div>
      {loading && <p>Loading photos...</p>}
      {error && <p className="text-danger">{error}</p>}
      {!loading && !error && photos.length > 0 && (
        <div className="row">
          {photos.slice(0, 10).map((photo) => (
            <div key={photo.id} className="col-md-4 mb-3">
              <img
                src={photo.img_src}
                alt={`Mars ${rover} rover image`}
                className="img-fluid"
                style={{ maxHeight: '200px' }}
              />
              <p>Sol: {photo.sol}, Camera: {photo.camera.full_name}</p>
            </div>
          ))}
        </div>
      )}
      {!loading && !error && photos.length === 0 && <p>No photos found for this sol.</p>}
    </div>
  );
};

export default MarsTab;
