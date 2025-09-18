# NASA Space Data Hub

## Overview

The NASA Space Data Hub is a unified API and interactive dashboard that aggregates multiple NASA datasets into a single, developer-friendly platform. The project consolidates scattered NASA APIs (Exoplanet Archive, ISS tracking, Mars rover data, APOD, and more) into one cohesive system with a modern React frontend and FastAPI backend. The goal is to make NASA's vast collection of space data easily accessible to developers, educators, and citizens through a simplified interface and intelligent search capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI (Python) providing RESTful API endpoints
- **API Aggregation Layer**: Modular structure with separate API modules for different NASA services:
  - `api/exoplanets.py` - NASA Exoplanet Archive integration
  - `api/iss.py` - ISS tracking and position data
  - `api/mars.py` - Mars rover photos, APOD, and other planetary data
- **Server Structure**: Single FastAPI application (`server/server.py`) that imports and orchestrates all API modules
- **CORS Configuration**: Enabled for cross-origin requests to support frontend communication
- **Error Handling**: Comprehensive exception handling with logging for API failures

### Frontend Architecture
- **Framework**: React 18+ with Create React App
- **UI Library**: React Bootstrap for responsive design
- **Data Visualization**: React Plotly.js for charts and graphs
- **HTTP Client**: Axios for API communication
- **Component Structure**: Tab-based interface with dedicated components for each data source:
  - ExoplanetsTab - Discovery timeline and filtering
  - MarsTab - Rover photo gallery
  - IssTab - Real-time ISS position tracking
- **Proxy Configuration**: Development proxy to backend on port 8000

### Data Processing
- **Query Building**: Dynamic SQL query construction for NASA Exoplanet Archive
- **Real-time Updates**: 5-second refresh intervals for ISS position data
- **Data Transformation**: JSON response processing and visualization data preparation
- **Filtering Capabilities**: Year-based filtering for exoplanet discovery data

### Development Workflow
- **Concurrent Development**: Uses concurrently to run both frontend and backend simultaneously
- **Testing Suite**: Comprehensive testing scripts for API endpoints validation
- **Environment Configuration**: Support for both DEMO_KEY and custom NASA API keys

## External Dependencies

### NASA APIs
- **Exoplanet Archive TAP Service** - Caltech IPAC hosted SQL-queryable database
- **ISS Location API** - wheretheiss.at for real-time ISS tracking
- **NASA APOD API** - Astronomy Picture of the Day service
- **Mars Rover Photos API** - Mission imagery from Curiosity, Perseverance, Opportunity
- **Near Earth Objects (NeoWs)** - Asteroid and comet tracking
- **EPIC (Earth Polychromatic Imaging Camera)** - Earth imagery
- **EONET (Earth Observatory Natural Events)** - Natural disaster tracking
- **DONKI** - Space weather and solar activity data
- **InSight** - Mars weather and seismic data
- **OSDR (Open Science Data Repository)** - Space biology experiments

### Third-party Services
- **wheretheiss.at** - ISS orbital tracking and position calculations
- **NASA Image and Video Library** - Media search and retrieval

### Runtime Dependencies
- **Backend**: FastAPI, requests, uvicorn for server hosting
- **Frontend**: React, React Bootstrap, Plotly.js, Axios
- **Development**: Concurrently for parallel process management
- **Testing**: FastAPI TestClient for endpoint validation

### API Authentication
- Supports both NASA DEMO_KEY (rate-limited) and custom API keys via environment variables
- Graceful degradation when API limits are reached
- Environment variable management for secure key storage
