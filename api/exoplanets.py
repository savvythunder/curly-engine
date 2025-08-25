import requests
from typing import Optional

db_tables = [
    "ps", "pscomppars", "toi", "ml", "stellarhosts", "keplernames", "k2names",
    "k2pandc", "spectra", "ukirttimeseries", "kelttimeseries",
    "superwasptimeseries", "di_stars_exep", "TD", "cumulative", "q1_q6_koi",
    "q1_q8_koi", "q1_q12_koi", "q1_q16_koi", "q1_q17_dr24_koi",
    "q1_q17_dr25_koi", "q1_q17_dr25_sup_koi", "q1_q12_tce", "q1_q16_tce",
    "q1_q17_dr24_tce", "q1_q17_dr25_tce", "keplerstellar", "q1_q12_ks",
    "q1_q16_ks", "q1_q17_dr24_ks", "q1_q17_dr25_ks", "q1_q17_dr25_sup_ks",
    "keplertimeseries", "k2targets"
]

base_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
required_param = "query="
params = [
    "select=",  # Specifies which columns within the chosen table to return. Columns must use a valid column name.
    "count=",  # Specifies the maximum number of rows to return."
    "where=",  # Specifies a condition to filter the rows returned.
    "order=",  # Specifies the order in which to return the rows.
    "ra=",  # Specifies the right ascension of the center of the search cone."
    "dec=",  # Specifies the declination of the center of the search cone."
    "radius=",  # Specifies the radius of the search cone."
    "format=",  # Specifies the format of the returned data. Options are json, csv, ipac, and tsv."
]
"""
Allowed Parameters
==================

These parameters can be passed as keyword arguments when building an API query.

Parameters
----------

table : str (required)
    Specifies which table to query.
    - Must be one of the valid table names from the Exoplanet Archive.
    - Example:
        table="q1_q16_koi"

select : str
    Specifies which columns to return.
    - One column:
        select="columnname"
    - Multiple columns:
        select="columnname1,columnname2,columnname3"
    - Distinct values:
        select="distinct columnname1,columnname2"
    - All columns:
        select="*"
    - Default columns:
        select="defaults"
    - Column names are case-insensitive.

    Special case:
    - Count rows:
        select="count(*)"

where : str
    Specifies row filtering conditions.
    - Greater than:
        where="dec>0"
    - Less than:
        where="dec<0"
    - String match:
        where="kepler_name like 'Kepler-52 c'"
    - Null values:
        where="kepler_name is null"
    - Multiple conditions:
        where="discoverymethod like 'Microlensing' and st_nts>0"

    Notes:
    - Wildcards must be URL-encoded as "%25".
    - Values are case-sensitive.

order : str
    Controls row ordering.
    - Ascending (default):
        order="dec"
    - Descending:
        order="dec desc"
    - Multiple columns:
        order="pl_hostname,pl_letter"

ra, dec, radius : float
    Defines a cone search in the sky.
    - Example (1 degree radius):
        ra=291, dec=48, radius="1 degree"
    - Units: degrees, arcmins, arcsecs.
    - Returned columns always include:
        ra, dec, dist (arcsec), angle (degrees)

format : str
    Specifies output format. Defaults to CSV.
    Options:
        - "csv" (default)
        - "ascii", "ipac", "ipac-ascii", "ipacascii", "ipac_ascii"
        - "bar", "bardelimited", "bar-delimited",
          "pipe", "pipedelimited", "pipe-delimited"
        - "xml", "votable", "vo-table", "vo_table"
        - "json" (case-insensitive)

Examples
--------

# Query specific table
query(table="q1_q16_koi")

# Select multiple columns
query(table="cumulative", select="pl_name,discoverymethod,disc_year")

# Count rows with conditions
query(table="ps", select="count(*)", where="ra>45")

# Cone search with filters
query(table="ps", ra=291, dec=48, radius="1 degree",
      select="pl_hostname,pl_letter,ra,dec",
      order="pl_hostname,pl_letter")

# JSON output
query(table="pscomppars", format="json")
"""


def get_exoplanet(table: str,
                  select: Optional[str] = None,
                  where: Optional[str] = None,
                  order: Optional[str] = None,
                  ra: Optional[float] = None,
                  dec: Optional[float] = None,
                  radius: Optional[float] = None,
                  format: Optional[str] = None) -> str | None:
    # Build SQL query for TAP service
    query = f"select {select or '*'} from {table}"
    if where:
        query += f" where {where}"
    if order:
        query += f" order by {order}"

    # URL encode the query and add format
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    url = base_url + required_param + encoded_query

    if format:
        url += f"&format={format}"

    print(f"DEBUG: SQL Query: {query}")
    print(f"DEBUG: Making request to: {url}")
    response = requests.get(url)
    print(f"DEBUG: Response status: {response.status_code}")
    print(f"DEBUG: Response headers: {response.headers}")
    print(f"DEBUG: Response content (first 200 chars): {response.text[:200]}")

    if response.status_code == 200:
        if format and format.lower() == "json":
            try:
                return response.json()
            except ValueError as e:
                print(f"DEBUG: JSON parsing failed: {e}")
                return None
        else:
            # Return raw text for other formats
            return response.text
    else:
        print(f"DEBUG: Request failed with status {response.status_code}")
        return None
