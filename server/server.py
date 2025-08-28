from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any, Union, Tuple
import sys
import os
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
import difflib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import from api modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from api.exoplanets import get_exoplanet, db_tables
    from api.iss import (get_iss_position, get_iss_tle, satellites,
                         get_coordinates_info, is_iss_overhead)
    from api.mars import (apod, Neow, CuriosityRover, NasaImages, Epic, Donki,
                          Eonet, OSDR, InSight)
    print("✅ All API modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

app = FastAPI(
    title="NASA Space Data Hub API",
    description=
    "Advanced Unified API for NASA Exoplanet, ISS tracking, Mars data with intelligent NLP search",
    version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# SIMPLIFIED NLP AND QUERY PROCESSING
# ==============================================================================


class SimplifiedNLPProcessor:
    """Advanced Natural Language Processing for space-related queries"""

    def __init__(self):
        self.entity_synonyms = {
            "celestial_bodies": {
                "earth":
                ["earth", "terra", "world", "planet earth", "our planet"],
                "mars": ["mars", "red planet", "martian", "fourth planet"],
                "jupiter":
                ["jupiter", "jovian", "gas giant", "largest planet"],
                "sun": ["sun", "solar", "star", "our star", "sol"],
                "moon": ["moon", "lunar", "earth's moon", "satellite"],
                "venus": ["venus", "morning star", "evening star"],
                "saturn": ["saturn", "ringed planet"],
                "mercury": ["mercury", "innermost planet"],
                "uranus": ["uranus", "ice giant"],
                "neptune": ["neptune", "furthest planet"]
            },
            "spacecraft": {
                "iss": [
                    "iss", "international space station", "space station",
                    "orbital station"
                ],
                "curiosity": ["curiosity", "mars science laboratory", "msl"],
                "perseverance": ["perseverance", "mars 2020", "percy"],
                "opportunity": ["opportunity", "mer-b", "oppy"],
                "spirit": ["spirit", "mer-a"],
                "ingenuity": ["ingenuity", "mars helicopter", "helicopter"]
            },
            "instruments": {
                "navcam": ["navcam", "navigation camera", "nav cam"],
                "mastcam": ["mastcam", "mast camera", "color camera"],
                "mahli": ["mahli", "hand lens imager"],
                "chemcam": ["chemcam", "laser spectrometer"],
                "hazcam": ["hazcam", "hazard avoidance camera"]
            },
            "phenomena": {
                "exoplanet":
                ["exoplanet", "extrasolar planet", "planet", "worlds"],
                "asteroid": ["asteroid", "minor planet", "space rock", "neo"],
                "comet": ["comet", "dirty snowball", "ice body"],
                "solar_flare":
                ["solar flare", "flare", "solar activity", "sun eruption"],
                "cme": ["cme", "coronal mass ejection", "solar storm"]
            }
        }

        self.size_categories = {
            "earth-like": {
                "min":
                0.8,
                "max":
                1.25,
                "keywords":
                ["earth-like", "earth-sized", "earthlike", "terrestrial"]
            },
            "super-earth": {
                "min": 1.25,
                "max": 2.0,
                "keywords":
                ["super-earth", "super earth", "large terrestrial"]
            },
            "neptune-like": {
                "min": 2.0,
                "max": 6.0,
                "keywords": ["neptune-like", "mini-neptune", "sub-neptune"]
            },
            "jupiter-like": {
                "min": 6.0,
                "max": 25.0,
                "keywords": ["jupiter-like", "gas giant", "giant planet"]
            },
            "small": {
                "min": 0.0,
                "max": 1.25,
                "keywords": ["small", "tiny", "mini"]
            },
            "large": {
                "min": 4.0,
                "max": 100.0,
                "keywords": ["large", "big", "huge", "massive"]
            }
        }

        self.temporal_patterns = {
            "year_range": r'\b(19|20)\d{2}[-–—to\s]+(19|20)\d{2}\b',
            "single_year": r'\b(19|20)\d{2}\b',
            "decade": r'\b(19|20)\d{1}0s?\b',
            "recent": r'\b(recent|latest|new|current|now|today)\b',
            "last_period": r'\b(last|past)\s+(week|month|year|decade)\b',
            "since": r'\bsince\s+(19|20)\d{2}\b',
            "after": r'\bafter\s+(19|20)\d{2}\b',
            "before": r'\bbefore\s+(19|20)\d{2}\b'
        }

        self.coordinate_pattern = r'(-?\d{1,3}\.?\d*)\s*[,°]\s*(-?\d{1,3}\.?\d*)'
        self.sol_pattern = r'\bsol\s*(\d+)\b'
        self.distance_pattern = r'(\d+(?:\.\d+)?)\s*(light\s*years?|ly|parsecs?|pc|km|miles?|au)'

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Advanced query parsing with enhanced entity recognition"""
        parsed = {
            "original": query,
            "intent": self._classify_intent(query),
            "entities": self._extract_entities(query),
            "temporal": self._extract_temporal(query),
            "spatial": self._extract_spatial(query),
            "numerical": self._extract_numerical(query),
            "filters": self._extract_filters(query),
            "complexity": self._assess_complexity(query),
            "confidence": 0.0
        }

        # Calculate confidence score
        parsed["confidence"] = self._calculate_confidence(parsed, query)

        return parsed

    def _classify_intent(self, query: str) -> str:
        """Classify the user's intent based on query content"""
        query_lower = query.lower()

        intent_patterns = {
            "discovery":
            ["discover", "found", "detect", "identify", "search for", "find"],
            "tracking": [
                "position", "location", "overhead", "tracking", "orbit",
                "trajectory"
            ],
            "imagery":
            ["image", "photo", "picture", "visual", "camera", "snapshot"],
            "data_analysis":
            ["analyze", "compare", "statistics", "data", "trends"],
            "space_weather":
            ["weather", "flare", "storm", "cme", "solar activity"],
            "mission_info":
            ["mission", "rover", "spacecraft", "launch", "landing"],
            "temporal_query": ["when", "time", "date", "period", "duration"],
            "comparison":
            ["compare", "versus", "difference", "similar", "like"],
            "factual": ["what", "how", "why", "explain", "definition"]
        }

        for intent, keywords in intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent

        return "general_search"

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract and normalize entities using synonym matching"""
        entities = defaultdict(list)
        query_lower = query.lower()

        for category, entity_map in self.entity_synonyms.items():
            for canonical_name, synonyms in entity_map.items():
                for synonym in synonyms:
                    if synonym in query_lower:
                        if canonical_name not in entities[category]:
                            entities[category].append(canonical_name)

        return dict(entities)

    def _extract_temporal(self, query: str) -> Dict[str, Any]:
        """Enhanced temporal extraction with ranges and relative dates"""
        temporal = {}
        query_lower = query.lower()

        # Year ranges
        year_range_match = re.search(self.temporal_patterns["year_range"],
                                     query)
        if year_range_match:
            start_year = int(
                year_range_match.group(1) + year_range_match.group(2)[:2])
            end_year = int(
                year_range_match.group(3) + year_range_match.group(4)[:2])
            temporal["year_range"] = [start_year, end_year]

        # Single year
        year_match = re.search(self.temporal_patterns["single_year"], query)
        if year_match and "year_range" not in temporal:
            temporal["year"] = int(year_match.group())

        # Relative time
        if re.search(self.temporal_patterns["recent"], query_lower):
            temporal["relative"] = "recent"
            temporal["since_year"] = datetime.now().year - 2

        # Since/after patterns
        since_match = re.search(self.temporal_patterns["since"], query_lower)
        if since_match:
            temporal["since_year"] = int(since_match.group(1))

        after_match = re.search(self.temporal_patterns["after"], query_lower)
        if after_match:
            temporal["after_year"] = int(after_match.group(1))

        return temporal

    def _extract_spatial(self, query: str) -> Dict[str, Any]:
        """Extract coordinates and spatial references"""
        spatial = {}

        # Coordinate patterns
        coord_match = re.search(self.coordinate_pattern, query)
        if coord_match:
            lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
            spatial["coordinates"] = {"latitude": lat, "longitude": lon}

        # Distance constraints
        distance_match = re.search(self.distance_pattern, query.lower())
        if distance_match:
            value = float(distance_match.group(1))
            unit = distance_match.group(2).replace(" ", "")
            spatial["distance"] = {"value": value, "unit": unit}

        return spatial

    def _extract_numerical(self, query: str) -> Dict[str, Any]:
        """Extract numerical values and constraints"""
        numerical = {}

        # Sol numbers
        sol_match = re.search(self.sol_pattern, query.lower())
        if sol_match:
            numerical["sol"] = int(sol_match.group(1))

        # General numbers that might be relevant
        number_matches = re.findall(r'\b(\d+(?:\.\d+)?)\b', query)
        if number_matches:
            numerical["values"] = [float(x) for x in number_matches]

        return numerical

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract search filters and constraints"""
        filters = {}
        query_lower = query.lower()

        # Size categories
        for category, info in self.size_categories.items():
            if any(keyword in query_lower for keyword in info["keywords"]):
                filters["size_category"] = category
                filters["radius_range"] = {
                    "min": info["min"],
                    "max": info["max"]
                }
                break

        # Habitable zone
        habitable_keywords = [
            "habitable", "goldilocks", "life", "livable", "habitation"
        ]
        if any(keyword in query_lower for keyword in habitable_keywords):
            filters["habitable_zone"] = True

        # Star types
        star_keywords = {
            "sun-like": ["sun-like", "solar-type", "g-type", "solar analog"],
            "red-dwarf": ["red dwarf", "m-dwarf", "m-type"],
            "hot": ["hot", "massive", "o-type", "b-type"]
        }

        for star_type, keywords in star_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                filters["star_type"] = star_type
                break

        return filters

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity based on multiple factors"""
        complexity_score = 0

        # Length factor
        if len(query.split()) > 10:
            complexity_score += 1

        # Multiple entities
        entity_count = sum(
            len(entities)
            for entities in self._extract_entities(query).values())
        if entity_count > 2:
            complexity_score += 1

        # Temporal constraints
        if len(self._extract_temporal(query)) > 1:
            complexity_score += 1

        # Multiple conditions
        condition_words = ["and", "or", "but", "with", "without", "except"]
        if any(word in query.lower() for word in condition_words):
            complexity_score += 1

        # Numerical constraints
        if len(self._extract_numerical(query)) > 1:
            complexity_score += 1

        if complexity_score >= 3:
            return "complex"
        elif complexity_score >= 1:
            return "moderate"
        else:
            return "simple"

    def _calculate_confidence(self, parsed: Dict[str, Any],
                              query: str) -> float:
        """Calculate confidence score for query interpretation"""
        confidence = 0.5  # Base confidence

        # Intent clarity
        if parsed["intent"] != "general_search":
            confidence += 0.1

        # Entity recognition
        entity_count = sum(
            len(entities) for entities in parsed["entities"].values())
        confidence += min(entity_count * 0.1, 0.2)

        # Temporal specificity
        if parsed["temporal"]:
            confidence += 0.1

        # Filter clarity
        if parsed["filters"]:
            confidence += 0.1

        # Query structure
        if len(query.split()) >= 3:  # Not too short
            confidence += 0.1

        return min(confidence, 1.0)


# Initialize NLP processor
nlp_processor = SimplifiedNLPProcessor()

# ==============================================================================
# ENHANCED SEARCH FUNCTIONS
# ==============================================================================


def fuzzy_match_names(query_name: str,
                      available_names: List[str],
                      threshold: float = 0.6) -> List[Tuple[str, float]]:
    """Fuzzy matching for planet/object names"""
    matches = []
    for name in available_names:
        ratio = difflib.SequenceMatcher(None, query_name.lower(),
                                        name.lower()).ratio()
        if ratio >= threshold:
            matches.append((name, ratio))
    return sorted(matches, key=lambda x: x[1], reverse=True)


def calculate_relevance_score(item: Dict[str, Any], parsed_query: Dict[str,
                                                                       Any],
                              query: str) -> float:
    """Multi-factor relevance scoring"""
    score = 0.0
    query_lower = query.lower()

    # Name matching (highest weight)
    if "pl_name" in item and item["pl_name"]:
        name_lower = str(item["pl_name"]).lower()
        for word in query_lower.split():
            if word in name_lower:
                score += 0.4

    # Temporal relevance
    if "disc_year" in item and item["disc_year"]:
        year = item["disc_year"]
        temporal = parsed_query.get("temporal", {})

        if "year" in temporal and year == temporal["year"]:
            score += 0.3
        elif "year_range" in temporal:
            start, end = temporal["year_range"]
            if start <= year <= end:
                score += 0.25
        elif "since_year" in temporal and year >= temporal["since_year"]:
            score += 0.2
        elif "recent" in temporal and year >= 2020:
            score += 0.15

    # Size relevance
    if "pl_rade" in item and item["pl_rade"]:
        radius = item["pl_rade"]
        filters = parsed_query.get("filters", {})

        if "radius_range" in filters:
            min_r, max_r = filters["radius_range"]["min"], filters[
                "radius_range"]["max"]
            if min_r <= radius <= max_r:
                score += 0.2

    # Habitable zone bonus
    if "pl_orbsmax" in item and item["pl_orbsmax"]:
        orbit = item["pl_orbsmax"]
        if parsed_query.get("filters",
                            {}).get("habitable_zone") and 0.7 <= orbit <= 1.5:
            score += 0.15

    # Distance relevance (closer is better for exoplanets)
    if "sy_dist" in item and item["sy_dist"]:
        distance = item["sy_dist"]
        if distance <= 50:  # Within 50 light years
            score += 0.1
        elif distance <= 100:
            score += 0.05

    # Intent-specific bonuses
    intent = parsed_query.get("intent", "")
    if intent == "discovery" and "disc_year" in item and item[
            "disc_year"] and item["disc_year"] >= 2015:
        score += 0.1

    return score


def search_exoplanets_advanced(
        query: str, parsed_query: Dict[str, Any], limit: int,
        advanced_filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Enhanced exoplanet search with comprehensive filtering"""
    try:
        where_conditions = []

        # Temporal filters
        temporal = parsed_query.get("temporal", {})
        if "year" in temporal:
            where_conditions.append(f"disc_year={temporal['year']}")
        elif "year_range" in temporal:
            start, end = temporal["year_range"]
            where_conditions.append(f"disc_year>={start} and disc_year<={end}")
        elif "since_year" in temporal:
            where_conditions.append(f"disc_year>={temporal['since_year']}")
        elif "after_year" in temporal:
            where_conditions.append(f"disc_year>{temporal['after_year']}")
        elif "recent" in temporal or "since_year" in temporal:
            since_year = temporal.get("since_year", 2020)
            where_conditions.append(f"disc_year>={since_year}")

        # Size filters
        filters = parsed_query.get("filters", {})
        if "radius_range" in filters:
            min_r, max_r = filters["radius_range"]["min"], filters[
                "radius_range"]["max"]
            where_conditions.append(f"pl_rade>={min_r} and pl_rade<={max_r}")

        # Habitable zone
        if filters.get("habitable_zone"):
            where_conditions.append("pl_orbsmax>=0.7 and pl_orbsmax<=1.5")

        # Star type filters
        star_type = filters.get("star_type")
        if star_type == "sun-like":
            where_conditions.append("st_teff>=5200 and st_teff<=6000")
        elif star_type == "red-dwarf":
            where_conditions.append("st_teff<4000")
        elif star_type == "hot":
            where_conditions.append("st_teff>8000")

        # Distance constraints
        spatial = parsed_query.get("spatial", {})
        if "distance" in spatial:
            dist_value = spatial["distance"]["value"]
            dist_unit = spatial["distance"]["unit"]

            # Convert to light years if needed
            if "ly" in dist_unit or "light" in dist_unit:
                where_conditions.append(f"sy_dist<={dist_value}")
            elif "pc" in dist_unit or "parsec" in dist_unit:
                ly_value = dist_value * 3.26
                where_conditions.append(f"sy_dist<={ly_value}")

        # Advanced filters from API
        if "min_distance" in advanced_filters:
            where_conditions.append(
                f"sy_dist>={advanced_filters['min_distance']}")
        if "max_distance" in advanced_filters:
            where_conditions.append(
                f"sy_dist<={advanced_filters['max_distance']}")
        if "min_mass" in advanced_filters:
            where_conditions.append(
                f"pl_masse>={advanced_filters['min_mass']}")
        if "max_mass" in advanced_filters:
            where_conditions.append(
                f"pl_masse<={advanced_filters['max_mass']}")

        where_clause = " and ".join(
            where_conditions) if where_conditions else None

        # Enhanced column selection
        select_columns = [
            "pl_name", "pl_rade", "pl_masse", "disc_year", "st_teff",
            "sy_dist", "pl_orbsmax", "st_spectype", "disc_facility",
            "pl_orbper", "pl_eqt", "sy_kepmag", "st_rad", "st_mass"
        ]

        result = get_exoplanet(table="ps",
                               select=",".join(select_columns),
                               where=where_clause,
                               order="disc_year desc",
                               format="json")

        if result and isinstance(result, list):
            # Add relevance scores
            for item in result:
                item["_relevance_score"] = calculate_relevance_score(
                    item, parsed_query, query)

            # Sort by relevance
            result.sort(key=lambda x: x.get("_relevance_score", 0),
                        reverse=True)

            # Limit results
            if len(result) > limit:
                result = result[:limit]

            return {
                "source": "NASA Exoplanet Archive",
                "count": len(result),
                "data": result,
                "query_interpretation": {
                    "where_conditions": where_conditions,
                    "parsed_query": parsed_query
                },
                "confidence": parsed_query.get("confidence", 0.8)
            }

    except Exception as e:
        print(f"Error in advanced exoplanet search: {e}")

    return None


def search_mars_comprehensive(query: str, parsed_query: Dict[str, Any],
                              limit: int) -> Optional[Dict[str, Any]]:
    """Comprehensive Mars data search across multiple sources"""
    try:
        results = []
        query_lower = query.lower()

        # APOD search
        if any(word in query_lower
               for word in ["picture", "image", "photo", "apod", "astronomy"]):
            try:
                count = min(limit // 2, 5)
                apod_result = apod(count=count)
                if apod_result:
                    results.append({
                        "type": "apod",
                        "source": "NASA APOD",
                        "data": apod_result,
                        "relevance_score": 0.8
                    })
            except Exception as e:
                print(f"APOD search error: {e}")

        # Mars rover photos
        entities = parsed_query.get("entities", {})
        numerical = parsed_query.get("numerical", {})

        if any(word in query_lower for word in
               ["rover", "mars", "curiosity", "perseverance", "sol"]):
            try:
                sol = numerical.get("sol", 1000)

                # Try multiple rovers
                rovers = ["curiosity", "perseverance", "opportunity"]
                for rover_name in rovers:
                    if rover_name in query_lower or "rover" in query_lower:
                        rover = CuriosityRover()

                        # Determine camera type
                        camera = None
                        instruments = entities.get("instruments", [])
                        if instruments:
                            camera = instruments[0]
                        elif "navcam" in query_lower:
                            camera = "navcam"
                        elif "mastcam" in query_lower:
                            camera = "mastcam"

                        photos = rover.photos_by_sol(rover_name,
                                                     sol,
                                                     camera=camera,
                                                     page=1)
                        if photos and photos.get("photos"):
                            limited_photos = photos["photos"][:limit // 3]
                            results.append({
                                "type": "rover_photos",
                                "source": f"Mars {rover_name.title()} Rover",
                                "sol": sol,
                                "camera": camera,
                                "data": limited_photos,
                                "relevance_score": 0.9
                            })
                        break
            except Exception as e:
                print(f"Rover search error: {e}")

        # Near Earth Objects
        if any(word in query_lower
               for word in ["asteroid", "neo", "near earth"]):
            try:
                neow = Neow()
                neo_data = neow.neo_feed()
                if neo_data:
                    results.append({
                        "type": "neo",
                        "source": "Near Earth Objects",
                        "data": neo_data,
                        "relevance_score": 0.7
                    })
            except Exception as e:
                print(f"NEO search error: {e}")

        # Space weather
        if any(word in query_lower
               for word in ["weather", "flare", "storm", "cme", "solar"]):
            try:
                donki = Donki()

                # Solar flares
                flare_data = donki.flr()
                if flare_data:
                    results.append({
                        "type": "solar_flares",
                        "source": "DONKI Space Weather",
                        "data": flare_data,
                        "relevance_score": 0.8
                    })

                # CME data
                cme_data = donki.cme()
                if cme_data:
                    results.append({
                        "type": "cme",
                        "source": "DONKI Space Weather",
                        "data": cme_data,
                        "relevance_score": 0.8
                    })

            except Exception as e:
                print(f"Space weather search error: {e}")

        # Earth observation
        if any(word in query_lower
               for word in ["earth", "epic", "observation"]):
            try:
                epic = Epic()
                earth_images = epic.natural_latest()
                if earth_images:
                    results.append({
                        "type": "earth_images",
                        "source": "EPIC Earth Images",
                        "data": earth_images[:limit // 4],
                        "relevance_score": 0.7
                    })
            except Exception as e:
                print(f"Earth observation search error: {e}")

        # Natural events
        if any(word in query_lower for word in
               ["event", "natural", "disaster", "fire", "volcano"]):
            try:
                eonet = Eonet()
                events = eonet.events(limit=limit // 4)
                if events:
                    results.append({
                        "type": "natural_events",
                        "source": "EONET Natural Events",
                        "data": events,
                        "relevance_score": 0.6
                    })
            except Exception as e:
                print(f"Natural events search error: {e}")

        if results:
            # Sort by relevance
            results.sort(key=lambda x: x.get("relevance_score", 0),
                         reverse=True)

            return {
                "source": "Mars & NASA Multi-API",
                "count": len(results),
                "data": results,
                "query_interpretation": parsed_query
            }

    except Exception as e:
        print(f"Error in comprehensive Mars search: {e}")

    return None


def search_iss_enhanced(query: str, parsed_query: Dict[str, Any],
                        limit: int) -> Optional[Dict[str, Any]]:
    """Enhanced ISS search with position tracking and predictions"""
    try:
        results = []
        query_lower = query.lower()

        if any(word in query_lower for word in
               ["iss", "station", "space station", "international", "orbit"]):
            # Current position
            position = get_iss_position(units="kilometers", timestamps=True)
            if position:
                result_item = {
                    "type": "current_position",
                    "source": "ISS Tracking API",
                    "data": position,
                    "live_data": True,
                    "relevance_score": 1.0
                }

                # Check if overhead at specific coordinates
                spatial = parsed_query.get("spatial", {})
                if "coordinates" in spatial:
                    coords = spatial["coordinates"]
                    overhead = is_iss_overhead(coords["latitude"],
                                               coords["longitude"])
                    coord_info = get_coordinates_info(coords["latitude"],
                                                      coords["longitude"])

                    result_item["overhead_check"] = {
                        "is_overhead": overhead,
                        "coordinates": coords,
                        "location_info": coord_info
                    }

                results.append(result_item)

            # TLE data for orbital calculations
            if "orbital" in query_lower or "tle" in query_lower:
                tle_data = get_iss_tle()
                if tle_data:
                    results.append({
                        "type": "tle_data",
                        "source": "ISS TLE Data",
                        "data": tle_data,
                        "relevance_score": 0.8
                    })

            # Satellite list
            if "satellite" in query_lower:
                sats = satellites()
                if sats:
                    results.append({
                        "type": "satellites",
                        "source": "Tracked Satellites",
                        "data": sats,
                        "relevance_score": 0.6
                    })

        if results:
            return {
                "source": "ISS Tracking System",
                "count": len(results),
                "data": results,
                "query_interpretation": parsed_query
            }

    except Exception as e:
        print(f"Error in enhanced ISS search: {e}")

    return None


def find_cross_dataset_correlations(
        datasets: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find intelligent correlations between datasets"""
    correlations = []

    try:
        # ISS and ground observations correlation
        if "iss" in datasets and "exoplanets" in datasets:
            correlations.append({
                "type":
                "observational_opportunity",
                "description":
                "ISS orbital path provides opportunities for ground-based telescope coordination",
                "datasets": ["iss", "exoplanets"],
                "significance":
                "medium",
                "context":
                "ISS position can be used to coordinate with ground observatories"
            })

        # Mars weather and rover operations
        if "mars" in datasets:
            mars_data = datasets["mars"]["data"]
            has_weather = any(
                item.get("type") in ["solar_flares", "cme"]
                for item in mars_data)
            has_rover = any(
                item.get("type") == "rover_photos" for item in mars_data)

            if has_weather and has_rover:
                correlations.append({
                    "type":
                    "operational_impact",
                    "description":
                    "Space weather events affect Mars rover operations and communication",
                    "datasets": ["mars"],
                    "significance":
                    "high",
                    "context":
                    "Solar activity can impact rover-Earth communications"
                })

        # Exoplanet discoveries and observation facilities
        if "exoplanets" in datasets:
            exo_data = datasets["exoplanets"]["data"]
            if isinstance(exo_data, list) and exo_data:
                facilities = set()
                for planet in exo_data:
                    if "disc_facility" in planet and planet["disc_facility"]:
                        facilities.add(planet["disc_facility"])

                if len(facilities) > 1:
                    correlations.append({
                        "type":
                        "discovery_method",
                        "description":
                        f"Multiple discovery facilities used: {', '.join(list(facilities)[:3])}",
                        "datasets": ["exoplanets"],
                        "significance":
                        "medium",
                        "context":
                        "Different telescopes excel at finding different types of planets"
                    })

    except Exception as e:
        print(f"Error finding correlations: {e}")

    return correlations


def generate_intelligent_suggestions(
        query: str, parsed_query: Dict[str, Any]) -> List[str]:
    """Generate context-aware search suggestions"""
    suggestions = []
    intent = parsed_query.get("intent", "general_search")
    entities = parsed_query.get("entities", {})

    # Intent-based suggestions
    if intent == "discovery":
        suggestions.extend([
            "Earth-sized exoplanets discovered since 2020 around sun-like stars",
            "Recent super-Earth discoveries in habitable zones within 100 light years",
            "Exoplanets found by James Webb Space Telescope"
        ])
    elif intent == "imagery":
        suggestions.extend([
            "Mars rover navcam images from sol 1500",
            "Latest Mars mastcam photos from Perseverance rover",
            "EPIC Earth observation images from last month"
        ])
    elif intent == "tracking":
        suggestions.extend([
            "ISS current position and next overhead pass",
            "International Space Station orbital trajectory this week",
            "ISS overhead passes for coordinates 40.7, -74.0"
        ])
    elif intent == "space_weather":
        suggestions.extend([
            "Recent solar flare activity and CME events",
            "Space weather impact on satellite operations",
            "Current geomagnetic storm conditions"
        ])

    # Entity-based suggestions
    if "mars" in entities.get("celestial_bodies", []):
        suggestions.append(
            "Mars atmospheric dust storm patterns and rover impact")
    if "iss" in entities.get("spacecraft", []):
        suggestions.append("ISS experimental modules and research activities")
    if "curiosity" in entities.get("spacecraft", []):
        suggestions.append(
            "Curiosity rover geological discoveries and sample analysis")

    # Trending and popular queries
    trending = [
        "James Webb telescope latest exoplanet atmospheric analysis",
        "Mars helicopter Ingenuity flight status and achievements",
        "Potentially habitable exoplanets with confirmed water vapor"
    ]

    # Combine and limit suggestions
    all_suggestions = suggestions + trending
    return list(
        dict.fromkeys(all_suggestions))[:5]  # Remove duplicates and limit


# ==============================================================================
# ORIGINAL ENDPOINTS (UNCHANGED)
# ==============================================================================


@app.get("/")
def read_root():
    try:
        return {
            "message":
            "NASA Space Data Hub API v2.0 - Enhanced with NLP",
            "status":
            "running",
            "endpoints": {
                "exoplanets": "/api/exoplanets/",
                "iss": "/api/iss/",
                "mars": "/api/mars/",
                "search": "/api/search/",
                "docs": "/docs",
                "health": "/health"
            },
            "features": [
                "Natural Language Processing",
                "Intelligent Query Interpretation",
                "Cross-Dataset Correlations", "Fuzzy Name Matching",
                "Comprehensive Search Results"
            ]
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return {"error": "Server error", "details": str(e)}


# EXOPLANETS ENDPOINTS
@app.get("/api/exoplanets/")
def get_exoplanets(
        table: str = Query(...,
                           description="Database table to query",
                           enum=db_tables),
        select: Optional[str] = Query("*", description="Columns to select"),
        where: Optional[str] = Query(None, description="Filter conditions"),
        order: Optional[str] = Query(None, description="Order by clause"),
        format: Optional[str] = Query("json",
                                      description="Output format",
                                      enum=["json", "csv", "xml"])):
    """Get exoplanet data from NASA Exoplanet Archive"""
    try:
        result = get_exoplanet(table=table,
                               select=select,
                               where=where,
                               order=order,
                               format=format)
        if result is None:
            raise HTTPException(status_code=404, detail="No data found")
        return {"data": result, "table": table, "format": format}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching exoplanet data: {str(e)}")


@app.get("/api/exoplanets/tables")
def get_available_tables():
    """Get list of available exoplanet database tables"""
    return {"tables": db_tables}


@app.get("/api/exoplanets/search")
def search_exoplanets(discovery_year: Optional[int] = Query(
    None, description="Discovery year"),
                      min_radius: Optional[float] = Query(
                          None,
                          description="Minimum planet radius (Earth radii)"),
                      max_radius: Optional[float] = Query(
                          None,
                          description="Maximum planet radius (Earth radii)"),
                      habitable_zone: Optional[bool] = Query(
                          None,
                          description="Filter for habitable zone planets")):
    """Search exoplanets with common filters"""
    try:
        where_conditions = []

        if discovery_year:
            where_conditions.append(f"disc_year={discovery_year}")
        if min_radius:
            where_conditions.append(f"pl_rade>={min_radius}")
        if max_radius:
            where_conditions.append(f"pl_rade<={max_radius}")
        if habitable_zone:
            where_conditions.append("pl_orbsmax>0.7 and pl_orbsmax<1.5")

        where_clause = " and ".join(
            where_conditions) if where_conditions else None

        result = get_exoplanet(
            table="ps",
            select="pl_name,pl_rade,disc_year,st_teff,sy_dist,pl_orbsmax",
            where=where_clause,
            order="disc_year desc",
            format="json")

        if result is None:
            raise HTTPException(status_code=404,
                                detail="No planets found matching criteria")

        return {"data": result, "filters_applied": where_conditions}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error searching exoplanets: {str(e)}")


# ISS ENDPOINTS
@app.get("/api/iss/")
def get_iss_current_position(units: Optional[str] = Query(
    "kilometers",
    description="Units for measurements",
    enum=["kilometers", "miles"]),
                             timestamps: Optional[bool] = Query(
                                 False,
                                 description="Include timestamp information")):
    """Get current ISS position and orbital data"""
    try:
        position = get_iss_position(units=units, timestamps=timestamps)
        if position is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch ISS position")
        return position
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching ISS position: {str(e)}")


@app.get("/api/iss/tle")
def get_iss_tle_data():
    """Get ISS Two-Line Element (TLE) orbital data"""
    try:
        tle_data = get_iss_tle()
        if tle_data is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch ISS TLE data")
        return tle_data
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching ISS TLE: {str(e)}")


@app.get("/api/iss/satellites")
def get_tracked_satellites():
    """Get list of all tracked satellites"""
    try:
        sats = satellites()
        return {"satellites": sats}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching satellites: {str(e)}")


@app.get("/api/iss/overhead/{latitude}/{longitude}")
def check_iss_overhead(
    latitude: float,
    longitude: float,
    altitude_threshold: Optional[float] = Query(
        500, description="Minimum altitude in km to consider overhead")):
    """Check if ISS is currently overhead at given coordinates"""
    try:
        overhead = is_iss_overhead(latitude, longitude, altitude_threshold)
        coords_info = get_coordinates_info(latitude, longitude)

        return {
            "is_overhead": overhead,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "altitude_threshold_km": altitude_threshold,
            "location_info": coords_info
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error checking ISS overhead: {str(e)}")


# MARS ENDPOINTS
@app.get("/api/mars/apod")
def get_astronomy_picture_of_day(
        date: Optional[str] = Query(None,
                                    description="Date in YYYY-MM-DD format"),
        start_date: Optional[str] = Query(None,
                                          description="Start date for range"),
        end_date: Optional[str] = Query(None,
                                        description="End date for range"),
        count: Optional[int] = Query(None,
                                     description="Number of random images"),
        thumbs: Optional[bool] = Query(
            False, description="Include video thumbnails")):
    """Get NASA Astronomy Picture of the Day"""
    try:
        if date and count:
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both 'date' and 'count' parameters")
        if date and (start_date or end_date):
            raise HTTPException(
                status_code=400,
                detail="Cannot specify 'date' with date range parameters")
        if count and (start_date or end_date):
            raise HTTPException(
                status_code=400,
                detail="Cannot specify 'count' with date range parameters")

        result = apod(date=date,
                      start_date=start_date,
                      end_date=end_date,
                      count=count,
                      thumbs=thumbs)
        if result is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch APOD data")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching APOD: {str(e)}")


@app.get("/api/mars/rover/{rover_name}/photos")
def get_rover_photos(
    rover_name: str,
    sol: Optional[int] = Query(None, description="Martian sol (day)"),
    earth_date: Optional[str] = Query(None,
                                      description="Earth date (YYYY-MM-DD)"),
    camera: Optional[str] = Query(None, description="Camera name"),
    page: Optional[int] = Query(1, description="Page number")):
    """Get Mars rover photos by sol or Earth date"""
    try:
        rover = CuriosityRover()

        if sol is not None:
            result = rover.photos_by_sol(rover_name, sol, camera, page)
        elif earth_date is not None:
            result = rover.photos_by_earth_date(rover_name, earth_date, camera,
                                                page)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either sol or earth_date parameter is required")

        if result is None:
            raise HTTPException(status_code=404, detail="No photos found")

        return result
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching rover photos: {str(e)}")


@app.get("/api/mars/rover/{rover_name}/manifest")
def get_rover_manifest(rover_name: str):
    """Get mission manifest for a Mars rover"""
    try:
        rover = CuriosityRover()
        result = rover.mission_manifest(rover_name)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No manifest found for rover {rover_name}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching rover manifest: {str(e)}")


@app.get("/api/mars/neo/feed")
def get_neo_feed(start_date: Optional[str] = Query(
    None, description="Start date (YYYY-MM-DD)"),
                 end_date: Optional[str] = Query(
                     None, description="End date (YYYY-MM-DD)")):
    """Get Near Earth Objects approaching Earth"""
    try:
        neow = Neow()
        result = neow.neo_feed(start_date, end_date)
        if result is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch NEO data")
        return result
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching NEO feed: {str(e)}")


@app.get("/api/mars/neo/{asteroid_id}")
def get_asteroid_details(asteroid_id: str):
    """Get details for a specific asteroid by NASA JPL ID"""
    try:
        neow = Neow()
        result = neow.neo_lookup(asteroid_id)
        if result is None:
            raise HTTPException(status_code=404,
                                detail=f"Asteroid {asteroid_id} not found")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching asteroid details: {str(e)}")


@app.get("/api/mars/epic/natural")
def get_epic_natural_images(date: Optional[str] = Query(
    None, description="Date in YYYY-MM-DD format")):
    """Get EPIC natural color Earth images"""
    try:
        epic = Epic()
        if date:
            result = epic.natural_by_date(date)
        else:
            result = epic.natural_latest()

        if result is None:
            raise HTTPException(status_code=404, detail="No EPIC images found")
        return {"images": result}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching EPIC images: {str(e)}")


@app.get("/api/mars/space-weather/cme")
def get_coronal_mass_ejections():
    """Get Coronal Mass Ejection data"""
    try:
        donki = Donki()
        result = donki.cme()
        if result is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch CME data")
        return {"cme_events": result}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching CME data: {str(e)}")


@app.get("/api/mars/space-weather/solar-flares")
def get_solar_flares():
    """Get Solar Flare data"""
    try:
        donki = Donki()
        result = donki.flr()
        if result is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch solar flare data")
        return {"solar_flares": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching solar flare data: {str(e)}")


@app.get("/api/mars/natural-events")
def get_natural_events(
        status: Optional[str] = Query("open", description="Event status"),
        limit: Optional[int] = Query(10,
                                     description="Number of events to return"),
        days: Optional[int] = Query(None,
                                    description="Events from last N days")):
    """Get Earth natural events from EONET"""
    try:
        eonet = Eonet()
        result = eonet.events(status=status, limit=limit, days=days)
        if result is None:
            raise HTTPException(status_code=503,
                                detail="Unable to fetch natural events")
        return result
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching natural events: {str(e)}")


@app.get("/api/mars/images/search")
def search_nasa_images(
        q: str = Query(..., description="Search query"),
        media_type: Optional[str] = Query(
            None, description="Media type (image, video, audio)"),
        year_start: Optional[int] = Query(None, description="Start year"),
        year_end: Optional[int] = Query(None, description="End year")):
    """Search NASA Image and Video Library"""
    try:
        nasa_images = NasaImages()
        result = nasa_images.search(q, media_type, year_start, year_end)
        if result is None:
            raise HTTPException(status_code=404, detail="No images found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error searching NASA images: {str(e)}")


# ----------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
