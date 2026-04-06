"""LLM-based data extraction for iTunes and Billboard charts."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

MODEL = "gpt-5-mini"


class iTunesSong(BaseModel):
    """Represents a song from the iTunes worldwide chart."""
    rank: int = Field(description="Chart position")
    title: str = Field(description="Song title")
    artist: str = Field(description="Artist name(s)")
    
    
class iTunesChart(BaseModel):
    """Collection of iTunes chart songs."""
    songs: List[iTunesSong] = Field(description="List of songs in the chart")
    chart_date: Optional[str] = Field(default=None, description="Chart date if available")


class BillboardSong(BaseModel):
    """Represents a song from the Billboard Hot 100."""
    rank: int = Field(description="Current chart position")
    title: str = Field(description="Song title")
    artist: str = Field(description="Artist name(s)")
    last_week_rank: Optional[int] = Field(default=None, description="Last week's position")
    peak_rank: Optional[int] = Field(default=None, description="Peak position on chart")
    weeks_on_chart: Optional[int] = Field(default=None, description="Number of weeks on chart")


class BillboardChart(BaseModel):
    """Collection of Billboard Hot 100 songs."""
    songs: List[BillboardSong] = Field(description="List of songs in the Hot 100")
    chart_date: Optional[str] = Field(default=None, description="Chart week ending date")


# Cache directory for LLM responses - defined after classes to avoid import issues
def _get_cache_dir() -> Path:
    """Get or create the cache directory."""
    cache_dir = Path(__file__).parent / ".llm_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir
    """Collection of Billboard Hot 100 songs."""
    songs: List[BillboardSong] = Field(description="List of songs in the Hot 100")
    chart_date: Optional[str] = Field(default=None, description="Chart week ending date")


def fetch_webpage_content(url: str) -> str:
    """
    Fetch the HTML content from a webpage.
    
    Args:
        url: The URL to fetch
        
    Returns:
        HTML content as string
    """
    logger.info(f"Fetching webpage: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    logger.info(f"Successfully fetched {len(response.text)} bytes from {url}")
    return response.text


def extract_itunes_chart() -> iTunesChart:
    """
    Extract the top iTunes worldwide songs from kworb.net using GPT.
    Uses cached data if available to save on API calls.
    
    Returns:
        iTunesChart object containing the parsed songs
    """
    logger.info("Starting iTunes chart extraction...")
    
    # Check cache first
    cache_file = _get_cache_dir() / "itunes_chart.json"
    if cache_file.exists():
        logger.info(f"Loading iTunes chart from cache: {cache_file}")
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            chart = iTunesChart(**cached_data)
            logger.info(f"Loaded {len(chart.songs)} songs from cache")
            return chart
    
    logger.info("No cache found, fetching fresh data...")
    # Fetch the webpage
    url = "https://kworb.net/ww/"
    html_content = fetch_webpage_content(url)
    
    # Parse with BeautifulSoup to get cleaner text
    logger.info("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract the table content (kworb uses a table structure)
    table = soup.find('table')
    if not table:
        raise ValueError("Could not find chart table on page")
    
    table_text = table.get_text()
    logger.info(f"Extracted table with {len(table_text)} characters")
    
    # Initialize OpenAI client
    logger.info("Calling GPT-4o-mini for structured extraction...")
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Use structured output with GPT
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a data extraction assistant. Extract song chart data from the provided text.
                Separate the song title from the artist name. If multiple artists are listed, keep them together in the artist field.
                Extract the rank, title, and artist for each song."""
            },
            {
                "role": "user",
                "content": f"Extract the iTunes chart data from this table:\n\n{table_text[:8000]}"  # Limit to avoid token limits
            }
        ],
        response_format=iTunesChart,
    )
    
    chart = completion.choices[0].message.parsed
    logger.info(f"Successfully extracted {len(chart.songs)} songs from iTunes chart")
    
    # Save to cache
    logger.info(f"Saving iTunes chart to cache: {cache_file}")
    with open(cache_file, 'w') as f:
        json.dump(chart.model_dump(), f, indent=2)
    logger.info("iTunes chart extraction complete")
    
    return chart


def extract_billboard_hot100() -> BillboardChart:
    """
    Extract the Billboard Hot 100 chart from billboard.com using GPT.
    Uses cached data if available to save on API calls.
    
    Returns:
        BillboardChart object containing the parsed songs with full metadata
    """
    logger.info("Starting Billboard Hot 100 extraction...")
    
    # Check cache first
    cache_file = _get_cache_dir() / "billboard_hot100.json"
    if cache_file.exists():
        logger.info(f"Loading Billboard chart from cache: {cache_file}")
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            chart = BillboardChart(**cached_data)
            logger.info(f"Loaded {len(chart.songs)} songs from cache")
            return chart
    
    logger.info("No cache found, fetching fresh data...")
    # Fetch the webpage
    url = "https://www.billboard.com/charts/hot-100/"
    html_content = fetch_webpage_content(url)
    
    # Parse with BeautifulSoup
    logger.info("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract chart date if available
    chart_date_elem = soup.find('p', class_='c-tagline')
    chart_date = chart_date_elem.get_text().strip() if chart_date_elem else None
    if chart_date:
        logger.info(f"Found chart date: {chart_date}")
    
    # Get the main chart content
    chart_content = soup.find('div', class_='chart-results-list') or soup.find('main')
    if not chart_content:
        raise ValueError("Could not find chart content on page")
    
    chart_text = chart_content.get_text()
    logger.info(f"Extracted chart content with {len(chart_text)} characters")
    
    # Save raw HTML and parsed text for debugging
    debug_dir = _get_cache_dir() / "debug"
    debug_dir.mkdir(exist_ok=True)
    
    with open(debug_dir / "billboard_raw.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"Saved raw HTML to {debug_dir / 'billboard_raw.html'}")
    
    with open(debug_dir / "billboard_parsed.txt", 'w', encoding='utf-8') as f:
        f.write(chart_text)
    logger.info(f"Saved parsed text to {debug_dir / 'billboard_parsed.txt'}")
    
    # Count how many times we see numbers 1-100 in the text (rough indicator of songs)
    import re
    rank_matches = re.findall(r'\b([1-9]|[1-9][0-9]|100)\b', chart_text)
    logger.info(f"Found {len(rank_matches)} potential rank numbers in parsed text")
    
    # Try to count actual song entries by looking for chart-list items
    chart_items = soup.find_all('li', class_=re.compile(r'chart-list__element'))
    if chart_items:
        logger.info(f"Found {len(chart_items)} chart list items in HTML")
    else:
        logger.warning("Could not find chart-list__element items in HTML")
    
    # Check different possible structures
    chart_rows = soup.find_all('div', class_=re.compile(r'chart-list-item'))
    if chart_rows:
        logger.info(f"Found {len(chart_rows)} chart-list-item divs in HTML")
    
    # Initialize OpenAI client
    logger.info("Calling GPT for structured extraction...")
    logger.info(f"Total chart text length: {len(chart_text)} characters")
    
    # Send more text to capture all 100 songs - GPT-4o-mini can handle ~128k tokens
    text_to_send = chart_text#[:50000]  # Increased from 12000 to 50000
    logger.info(f"Sending {len(text_to_send)} characters to LLM")
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Use structured output with GPT
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a data extraction assistant. Extract ALL 100 songs from the Billboard Hot 100 chart data.
                For each song, extract:
                - Current rank (1-100)
                - Song title
                - Artist name(s)
                - Last week's rank (if available, otherwise null)
                - Peak rank on chart (if available, otherwise null)
                - Number of weeks on chart (if available, otherwise null)
                
                IMPORTANT: You must extract all 100 songs from the chart, not just the first few.
                The chart is numbered from 1 to 100. Make sure you capture every single entry."""
            },
            {
                "role": "user",
                "content": f"Extract ALL 100 songs from the Billboard Hot 100 chart data from this content:\n\n{text_to_send}"
            }
        ],
        response_format=BillboardChart,
    )
    
    chart = completion.choices[0].message.parsed
    if chart_date and not chart.chart_date:
        chart.chart_date = chart_date
    
    logger.info(f"Successfully extracted {len(chart.songs)} songs from Billboard Hot 100")
    
    if len(chart.songs) < 100:
        logger.warning(f"Expected 100 songs but only got {len(chart.songs)}")
        logger.info(f"First song: {chart.songs[0].title if chart.songs else 'None'}")
        logger.info(f"Last song: {chart.songs[-1].title if chart.songs else 'None'}")
        if len(chart.songs) > 0:
            logger.info(f"Rank range: {chart.songs[0].rank} - {chart.songs[-1].rank}")
    
    # Save LLM response for debugging
    debug_dir = _get_cache_dir() / "debug"
    with open(debug_dir / "billboard_llm_response.json", 'w', encoding='utf-8') as f:
        json.dump(chart.model_dump(), f, indent=2)
    logger.info(f"Saved LLM response to {debug_dir / 'billboard_llm_response.json'}")
    
    # Save to cache
    logger.info(f"Saving Billboard chart to cache: {cache_file}")
    with open(cache_file, 'w') as f:
        json.dump(chart.model_dump(), f, indent=2)
    logger.info("Billboard Hot 100 extraction complete")
    
    return chart


def get_itunes_artists() -> List[str]:
    """
    Get a list of unique artists from the iTunes chart.
    
    Returns:
        List of artist names
    """
    chart = extract_itunes_chart()
    return list(set(song.artist for song in chart.songs))


def get_billboard_artists() -> List[str]:
    """
    Get a list of unique artists from the Billboard Hot 100.
    
    Returns:
        List of artist names
    """
    chart = extract_billboard_hot100()
    return list(set(song.artist for song in chart.songs))
