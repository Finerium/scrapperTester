"""
Data storage: CSV writer, JSON writer, and progress checkpoint manager.
"""
import csv
import json
import os
import logging
from typing import List

from models import DrugInfo
from config import CSV_COLUMNS, CSV_FILE, JSON_FILE, PROGRESS_FILE, OUTPUT_DIR

logger = logging.getLogger(__name__)


class DataWriter:
    """Write drug data to CSV and JSON."""

    def __init__(self, csv_path: str = CSV_FILE, json_path: str = JSON_FILE):
        self.csv_path = csv_path
        self.json_path = json_path
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._init_csv()

    def _init_csv(self):
        """Write CSV header if file does not exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()

    def append_csv(self, drug: DrugInfo):
        """Append a single drug record to CSV."""
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writerow(drug.to_csv_row())

    def write_json(self, drugs: List[DrugInfo]):
        """Write the complete drug list to JSON (overwrite)."""
        data = [d.to_dict() for d in drugs]
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("JSON written: %d records to %s", len(data), self.json_path)


class ProgressTracker:
    """
    Checkpoint-based progress tracking for resumable scraping.
    Tracks completed letters, scraped URLs, and failed URLs.
    """

    def __init__(self, progress_file: str = PROGRESS_FILE):
        self.progress_file = progress_file
        self.state = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed_letters': [],
            'scraped_urls': [],
            'total_drugs_found': 0,
            'total_drugs_scraped': 0,
            'failed_urls': [],
        }

    def save(self):
        os.makedirs(os.path.dirname(self.progress_file) or '.', exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def is_letter_done(self, letter: str) -> bool:
        return letter in self.state['completed_letters']

    def is_url_scraped(self, url: str) -> bool:
        return url in self.state['scraped_urls']

    def mark_url_done(self, url: str):
        if url not in self.state['scraped_urls']:
            self.state['scraped_urls'].append(url)
            self.state['total_drugs_scraped'] += 1

    def mark_url_failed(self, url: str):
        if url not in self.state['failed_urls']:
            self.state['failed_urls'].append(url)

    def mark_letter_done(self, letter: str):
        if letter not in self.state['completed_letters']:
            self.state['completed_letters'].append(letter)

    def reset(self):
        """Reset all progress (for fresh start)."""
        self.state = {
            'completed_letters': [],
            'scraped_urls': [],
            'total_drugs_found': 0,
            'total_drugs_scraped': 0,
            'failed_urls': [],
        }
