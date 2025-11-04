"""
Time Doctor Scraper Package
A Python package for scraping and exporting Time Doctor time tracking data
"""

from .parser import TimeDocorParser
from .scraper import TimeDocorScraper
from .transformer import TimeDocorTransformer, export_to_csv, get_hours_summary

__version__ = "1.0.0"
__author__ = "Time Doctor Scraper"

__all__ = [
    "TimeDocorScraper",
    "TimeDocorParser",
    "TimeDocorTransformer",
    "export_to_csv",
    "get_hours_summary",
]
