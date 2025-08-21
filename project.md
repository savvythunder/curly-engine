 

 

 

This project is about building a **unified API + interactive dashboard** that lets people easily search, query, and visualize NASA datasets (and potentially other space agency datasets). 

 

 

## 🔭 Problem 

 

NASA has tons of **open datasets** — exoplanets, rover images, ISS telemetry, Earth observation, launch data, etc. 

But: 

 

* They are **scattered across multiple APIs** (Exoplanet Archive, EONET, EarthData, etc.). 

* Each has **different formats** (CSV, JSON, netCDF, HDF). 

* They can be **hard for developers, educators, or citizens** to use. 

 

So the challenge: **make NASA’s data accessible in one place.** 

 

 

## 🚀 Solution: Open Space Data Hub 

 

### Core Features 

 

**Unified API Layer** 

 

   * Aggregate multiple NASA APIs + datasets into **one developer-friendly endpoint**. 

   * Example: 

 

     ```http 

     GET /api/exoplanets?size=earthlike&star=G-type 

     GET /api/earth/temperature?lat=28.6&lon=77.2&year=2020 

     GET /api/mars/rovers/photos?sol=1000 

     ``` 

 

**Search & Filter Engine** 

 

   * Natural-language query support (e.g., “Show me habitable-zone exoplanets around sun-like stars”). 

   * Advanced filters (date range, location, mission). 

 

**Interactive Dashboard (Frontend)** 

 

   * Visualization of datasets in **charts, maps, timelines, and 3D models**. 

   * Exoplanets → 3D star maps 

   * Earth data → Heatmaps on world globe 

   * ISS telemetry → Real-time orbital tracker 

 

**Data Export** 

 

Let users export results in CSV, JSON, or even GIS formats for research. 

 

 

## ⚡ Example Use Cases 

 

* **Educators:** A teacher could show students “all the Earth-sized exoplanets in the habitable zone.” 

* **Researchers:** Quickly pull climate anomaly data for a specific region and time range. 

* **Developers:** Use the unified API for their own apps without juggling multiple NASA APIs. 

* **Public Enthusiasts:** Visualize ISS real-time orbit or browse Mars rover images interactively. 

 

 

## 🛠️ Tech Stack 

 

**Backend / API Layer** 

 

  * Python (FastAPI / Flask) or Node.js (Express) 

  * Middleware to fetch + normalize NASA APIs 

  * GraphQL layer for flexible querying (optional but powerful) 

 

**Frontend Dashboard** 

 

  * React / Next.js or Vue.js 

  * D3.js or Plotly for data visualizations 

  * CesiumJS or NASA WorldWind for 3D Earth/space visualizations 

 

**Data Sources (NASA APIs)** 

 

  * [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) 

  * [NASA EarthData](https://earthdata.nasa.gov/) 

  * [EONET (Earth Observatory Natural Event Tracker)](https://eonet.gsfc.nasa.gov/) 

  * [NASA Mars Rover Photos](https://api.nasa.gov/) 

  * [ISS Current Location](https://wheretheiss.at/) 

 

 

## 🎨 Demo Ideas for Hackathon 

 

* Start with **3 datasets**: Exoplanets, Mars Rover Images, ISS tracker. 

* Show a **single query + visualization pipeline**: 

 

  * Query → Backend fetches data → Unified format → Frontend visualization. 

* Example Demo Flow: 

 

  1. Type: “Show me all exoplanets discovered in 2023 with Earth-like radius.” 

  2. System returns results in a table + plots them on a **3D star map**. 

  3. Switch tab: See ISS orbit live on globe. 

  4. Switch tab: Browse Mars rover images by Sol. 

 

 

## 🏆 Why Judges Will Love It 

 

* Solves a **real pain point**: NASA data is powerful but hard to access. 

* **Scalable**: Start small, then expand to more datasets. 

* **Showy demo**: Interactive globe, 3D visualizations, live space data → instant wow factor. 

* **Practical impact**: Helps developers, educators, and researchers. 

 

 

 

Perfect 🚀 — since I’m going to use **Python**, we can set this up with **FastAPI (backend)** and a lightweight **React/Dash frontend** for visualization. 

Here’s a **step-by-step roadmap** to keep the project structured: 

 

 

# 📅 Roadmap for **Open Space Data Hub** 

 

 

## **Week 1 — Foundation (Backend + Core APIs)** 

 

✅ Goal: Have a working backend that fetches & normalizes NASA data. 

 

**Set up Backend (FastAPI + Python)** 

 

   * Create FastAPI project. 

   * Add endpoints like `/api/exoplanets`, `/api/mars`, `/api/iss`. 

 

**Integrate NASA APIs** 

 

   * Exoplanet Archive → Parse JSON/CSV and serve filtered results. 

   * Mars Rover Photos API → Fetch by Sol/Date. 

   * ISS Location API → Live orbit coordinates. 

 

**Data Normalization Layer** 

 

   * Convert different formats into a **consistent JSON structure**. 

   * Example output: 

 

     ```json 

     { 

       “dataset”: “exoplanets”, 

       “fields”: [“name”, “radius”, “discovery_year”, “distance”], 

       “results”: […] 

     } 

     ``` 

 

**Basic Testing** 

 

   * Test endpoints with Postman / curl. 

   * Make sure queries return correct data. 

 

 

## **Week 2 — Frontend & Visualization** 

 

✅ Goal: Build an interactive dashboard with charts and maps. 

 

**Frontend Setup** 

 

   * Use **React** (for flexibility) or **Dash (Plotly)** (if you want quicker dev). 

   * Connect frontend → backend API calls. 

 

**Data Visualization** 

 

   * Exoplanets → Scatter plots (radius vs. star type), discovery timeline. 

   * ISS → Live position on a globe (CesiumJS / Plotly globe). 

   * Mars Rovers → Image gallery with filters. 

 

**Basic UI** 

 

   * Navigation bar: *Exoplanets | Mars | ISS* 

   * Query form + visualization display. 

 

 

## **Week 3 — Advanced Features** 

 

✅ Goal: Make it more powerful + hackathon-demo ready. 

 

**Natural Language Query (Optional, Stretch Goal)** 

 

   * Use a lightweight NLP (e.g., spaCy or GPT API if allowed) → translate queries into filters. 

   * Example: “Earth-like planets discovered after 2015” → `radius ~ 1 earth & year > 2015`. 

 

**Export Options** 

 

Button to export results as CSV/JSON. 

 

**Improved Visuals** 

 

   * Exoplanets in **3D star map** (e.g., Three.js, Plotly 3D scatter). 

   * ISS orbit path over time. 

 

 

## **Week 4 — Polish & Demo Prep** 

 

✅ Goal: Have a polished MVP ready for hackathon demo. 

 

**UI Polish** 

 

   * Add branding + NASA-style theme. 

   * Improve loading states & error handling. 

 

**Documentation** 

 

   * README with: Setup, Features, API examples, Demo video link. 

   * API docs auto-generated from FastAPI (Swagger UI). 

 

**Hackathon Demo Flow** 

 

   * Start with a query: *“Show me all exoplanets discovered in 2023.”* 

   * Show them on a **timeline chart** + **3D star map**. 

   * Switch to ISS tab → Live tracking. 

   * Switch to Mars tab → Rover images gallery. 

   * Export results as CSV. 

 

 

# 🛠️ Tech Stack (Python-centric) 

 

* **Backend**: FastAPI + Requests/HTTPX for API calls, Pydantic for schemas 

* **Frontend**: 

 

  * Quick option: **Dash (Plotly)** → less setup, faster data visualization 

  * More scalable: **React + D3.js/Plotly + CesiumJS** 

* **Data Handling**: Pandas (for transformations) 

* **Deployment**: Docker + free hosting (Heroku, Vercel, or Render) 

 

 

👉 Tip: **don’t overbuild** — start with **3 datasets (Exoplanets, Mars Rover, ISS)**, nail the unified API + dashboard, then add stretch goals if time allows. 

Awesome 🙌 — let’s pick **3 solid NASA APIs** that are: 

✅ Easy to integrate with Python, 

✅ Give *cool visualizations for a hackathon demo*, 

✅ Cover different domains (space science, Earth/space ops, outreach). 

 

Here are the **best 3 to start with**: 

 

 

## **1. NASA Exoplanet Archive (Exoplanets Data)** 🌌 

 

🔗 [Exoplanet Archive API Docs](https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html) 

 

* **What it gives:** Thousands of confirmed exoplanets with details like size, star type, orbital period, discovery year. 

* **Why it’s great:** You can make discovery trend charts, scatter plots (size vs. distance), or a 3D star map. 

* **Python Example:** 

 

```python 

Import requests 

 

url = https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,disc_year,st_teff,sy_dist+from+ps&format=json 

data = requests.get(url).json() 

print(data[:2])  # print first 2 exoplanets 

``` 

 

📊 **Visualization Idea:** 

 

* Timeline → *How many planets discovered each year* 

* Bubble chart → *Planet radius vs. star temperature* 

* 3D → *Stars plotted in galactic coordinates* 

 

 

## **2. NASA Mars Rover Photos API (Mars Data)** 🤖 

 

🔗 [Mars Rover API Docs](https://api.nasa.gov/) 

 

* **What it gives:** Real images taken by Curiosity, Opportunity, and Perseverance rovers. 

* **Why it’s great:** Everyone loves **real Mars pictures** → perfect for a hackathon demo. 

* **Python Example:** 

 

```python 

Import requests 

 

API_KEY = “DEMO_KEY”  # replace with your NASA API key 

url = fhttps://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol=1000&camera=navcam&api_key={API_KEY} 

data = requests.get(url).json() 

print(data[‘photos’][0][‘img_src’]) 

``` 

 

📊 **Visualization Idea:** 

 

* Mars rover **image gallery** by Sol (Martian day). 

* Map rover landing site + path (stretch goal). 

 

 

## **3. ISS Current Location (ISS Live Data)** 🛰️ 

 

🔗 [Where The ISS At API](https://wheretheiss.at/w/developer) (community API but reliable) 

 

* **What it gives:** Real-time ISS position (lat, lon, altitude, velocity). 

* **Why it’s great:** Live tracking = immediate **wow factor** for demo. 

* **Python Example:** 

 

```python 

Import requests 

 

url = https://api.wheretheiss.at/v1/satellites/25544 

data = requests.get(url).json() 

print(f”ISS is at lat {data[‘latitude’]}, lon {data[‘longitude’]}”) 

``` 

 

📊 **Visualization Idea:** 

 

* Show ISS orbit on a **globe** (Plotly 3D globe or CesiumJS). 

* Plot past orbit trail for the last hour. 

 

 

# 🎯 Hackathon MVP Plan 

 

* **Backend:** FastAPI endpoints → `/api/exoplanets`, `/api/mars`, `/api/iss` 

* **Frontend Demo Flow:** 

 

  1. Search exoplanets by year → chart + 3D plot. 

  2. Switch to Mars tab → browse rover photos. 

  3. Switch to ISS tab → see live orbit moving in real time. 

 

This gives you a **multi-domain, interactive hub** without overwhelming scope. 

 

 

 

For visualization I’ll go with **Matplotlib** — it keeps things simple and Python-native. Since hackathons are about showing results quickly, Matplotlib is a safe choice. 

 

Here’s how each of the 3 datasets can be visualized with it: 

 

 

## **1. Exoplanets Data (from NASA Exoplanet Archive)** 🌌 

 

**Charts with Matplotlib:** 

 

  * **Timeline**: Number of exoplanets discovered per year. 

  * **Scatter Plot**: Planet radius vs. star temperature. 

  * **Histogram**: Distribution of orbital periods. 

 

```python 

Import requests, pandas as pd 

Import matplotlib.pyplot as plt 

 

# Fetch exoplanet data 

url = https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,disc_year,st_teff+from+ps&format=json 

data = requests.get(url).json() 

df = pd.DataFrame(data) 

 

# Discovery timeline 

Df[‘disc_year’] = pd.to_numeric(df[‘disc_year’], errors=’coerce’) 

Counts = df.groupby(‘disc_year’).size() 

 

Plt.figure(figsize=(10,5)) 

Counts.plot(kind=’bar’) 

Plt.title(“Exoplanets Discovered per Year”) 

Plt.xlabel(“Year”) 

Plt.ylabel(“Number of Planets”) 

Plt.show() 

``` 

 

 

## **2. Mars Rover Photos (from NASA Mars API)** 🤖 

 

**Charts with Matplotlib:** 

 

  * **Gallery**: You can fetch rover images and show them with `plt.imshow()`. 

  * **Photo Counts**: Bar chart of how many photos per camera. 

 

```python 

Import requests 

From PIL import Image 

From io import BytesIO 

Import matplotlib.pyplot as plt 

 

API_KEY = “DEMO_KEY” 

url = fhttps://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol=1000&camera=navcam&api_key={API_KEY} 

data = requests.get(url).json() 

 

# Display first image 

Img_url = data[‘photos’][0][‘img_src’] 

Img = Image.open(BytesIO(requests.get(img_url).content)) 

 

Plt.imshow(img) 

Plt.axis(“off”) 

Plt.title(“Mars Rover Image – Sol 1000”) 

Plt.show() 

``` 

 

 

## **3. ISS Current Location (WhereTheISSAt API)** 🛰️ 

 

**Charts with Matplotlib:** 

 

  * **2D Map**: Plot ISS position (lat, lon) on a world map. 

  * You can use **Basemap** or **Cartopy** (extensions for geospatial plotting). 

 

```python 

Import requests 

Import matplotlib.pyplot as plt 

 

# Get ISS position 

url = https://api.wheretheiss.at/v1/satellites/25544 

data = requests.get(url).json() 

lat, lon = data[‘latitude’], data[‘longitude’] 

 

# Simple 2D plot of Earth with ISS location 

Plt.figure(figsize=(8,4)) 

Plt.scatter(lon, lat, color=’red’, marker=’o’) 

Plt.title(“Current ISS Location”) 

Plt.xlabel(“Longitude”) 

Plt.ylabel(“Latitude”) 

Plt.xlim(-180, 180) 

Plt.ylim(-90, 90) 

Plt.grid(True) 

Plt.show() 

``` 

 

 

# ✅ Why Matplotlib Works Well 

 

* It’s **fast and hackathon-friendly**. 

* Easy to make bar charts, scatter plots, line graphs, and even show images. 

* You can extend it with **Basemap or Cartopy** for nicer Earth visualizations. 

 

⚡ Bonus: If you want more **interactive features** (hover, zoom, tooltips), you could still plug in **Plotly** later just for visuals — but for a clean Python-only stack, Matplotlib is perfect. 

 

 

 

 

 

 

 

 

 
