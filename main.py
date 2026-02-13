"""
drugs.com Web Scraper - Entry Point

Scrapes drug information from drugs.com alphabetical index pages,
using Patchright (patched Playwright) to bypass Cloudflare protection.

Usage:
    python main.py                          # Scrape all letters (headless)
    python main.py --no-headless            # Visible browser for debugging
    python main.py --letters a,b,c          # Specific letters only
    python main.py --resume                 # Resume from last checkpoint
    python main.py --log-level DEBUG        # Verbose logging
"""
import argparse
import logging
import os
import sys

from utils import setup_logging
from scraper import DrugsScraper
from config import PROGRESS_FILE


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape drug information from drugs.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --no-headless --letters x      Test with letter X (visible browser)
  python main.py --resume                       Resume from last checkpoint
  python main.py --letters a,b,c                Scrape only letters A, B, C
        """
    )
    parser.add_argument(
        '--no-headless', action='store_true',
        help='Run browser in visible mode (for debugging / verifying Cloudflare bypass)'
    )
    parser.add_argument(
        '--letters', type=str, default=None,
        help='Comma-separated letters to scrape, e.g., "a,b,c" (default: all a-z)'
    )
    parser.add_argument(
        '--log-level', type=str, default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='Resume from last checkpoint (skip already-scraped items)'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level)

    logger = logging.getLogger(__name__)

    # Parse options
    headless = not args.no_headless
    letters = None
    if args.letters:
        letters = [l.strip().lower() for l in args.letters.split(',')]
        invalid = [l for l in letters if len(l) != 1 or not l.isalpha()]
        if invalid:
            logger.error("Invalid letters: %s", invalid)
            sys.exit(1)

    # Handle resume
    if not args.resume and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        logger.info("Fresh start: cleared previous progress")

    # Run scraper
    scraper = DrugsScraper(headless=headless, letters=letters)
    scraper.run()


if __name__ == '__main__':
    main()
