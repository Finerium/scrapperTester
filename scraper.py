"""
Core scraping logic: orchestrates browser navigation and HTML parsing.
"""
import re
import logging
from typing import List, Optional, Tuple

from browser import BrowserManager
from parser import AlphaPageParser, DrugDetailParser, SideEffectsParser
from models import DrugInfo
from storage import DataWriter, ProgressTracker
from utils import random_delay, retry_on_failure
from config import (
    BASE_URL, ALPHA_URL_TEMPLATE, SIDE_EFFECTS_URL_TEMPLATE,
    LETTERS, HEADLESS, USER_DATA_DIR, CLOUDFLARE_WAIT,
)

logger = logging.getLogger(__name__)


class DrugsScraper:
    """Main scraper: iterates alpha pages, visits detail pages, extracts data."""

    def __init__(self, headless: bool = HEADLESS, letters: Optional[List[str]] = None):
        self.headless = headless
        self.letters = letters or LETTERS
        self.browser_mgr = BrowserManager(headless=headless, user_data_dir=USER_DATA_DIR)
        self.writer = DataWriter()
        self.progress = ProgressTracker()
        self.page = None
        self.all_drugs: List[DrugInfo] = []

    def run(self):
        """Main entry point: scrape all configured letters."""
        logger.info("=" * 60)
        logger.info("Starting drugs.com scraper")
        logger.info("Letters: %s", ', '.join(self.letters))
        logger.info("Headless: %s", self.headless)
        logger.info("=" * 60)

        self.browser_mgr.start()
        self.page = self.browser_mgr.new_page()

        try:
            for letter in self.letters:
                if self.progress.is_letter_done(letter):
                    logger.info("[%s] Skipping (already completed)", letter.upper())
                    continue

                logger.info("")
                logger.info("=" * 40)
                logger.info("[%s] Processing letter", letter.upper())
                logger.info("=" * 40)

                drug_links = self._scrape_alpha_pages(letter)
                logger.info("[%s] Found %d drugs total", letter.upper(), len(drug_links))

                for i, (name, url) in enumerate(drug_links, 1):
                    if self.progress.is_url_scraped(url):
                        logger.debug("[%s] Skipping %s (already scraped)", letter.upper(), name)
                        continue

                    logger.info("[%s] (%d/%d) Scraping: %s",
                                letter.upper(), i, len(drug_links), name)

                    drug_info = self._scrape_drug_detail(name, url)
                    if drug_info:
                        self.all_drugs.append(drug_info)
                        self.writer.append_csv(drug_info)
                        self.progress.mark_url_done(url)
                        logger.info("[%s] OK: %s | generic=%s | class=%s | rating=%s | side_effects=%d",
                                    letter.upper(), drug_info.name,
                                    drug_info.generic_name or '-',
                                    drug_info.drug_class or '-',
                                    drug_info.rating or '-',
                                    len(drug_info.side_effects))
                    else:
                        self.progress.mark_url_failed(url)
                        logger.warning("[%s] FAILED: %s", letter.upper(), name)

                    self.progress.save()
                    random_delay()

                self.progress.mark_letter_done(letter)
                self.progress.save()
                logger.info("[%s] Completed. Total scraped so far: %d",
                            letter.upper(), self.progress.state['total_drugs_scraped'])

            # Final JSON write
            self.writer.write_json(self.all_drugs)
            logger.info("")
            logger.info("=" * 60)
            logger.info("SCRAPING COMPLETE")
            logger.info("Total drugs scraped: %d", len(self.all_drugs))
            logger.info("Failed URLs: %d", len(self.progress.state['failed_urls']))
            logger.info("=" * 60)

        except KeyboardInterrupt:
            logger.warning("")
            logger.warning("Interrupted by user. Saving progress...")
            self.progress.save()
            if self.all_drugs:
                self.writer.write_json(self.all_drugs)
            logger.info("Progress saved. Use --resume to continue later.")

        except Exception as e:
            logger.error("Unexpected error: %s", e, exc_info=True)
            self.progress.save()
            if self.all_drugs:
                self.writer.write_json(self.all_drugs)
            raise

        finally:
            self.browser_mgr.close()

    def _scrape_alpha_pages(self, letter: str) -> List[Tuple[str, str]]:
        """Scrape all paginated pages for a given letter."""
        all_links = []
        page_num = 1
        current_url = ALPHA_URL_TEMPLATE.format(letter=letter)

        while current_url:
            logger.info("[%s] Fetching alpha page %d: %s", letter.upper(), page_num, current_url)

            html = self._fetch_page(current_url)
            if not html:
                logger.error("[%s] Failed to fetch alpha page %d", letter.upper(), page_num)
                break

            links = AlphaPageParser.parse_drug_links(html, BASE_URL)
            all_links.extend(links)
            logger.info("[%s] Page %d: found %d drug links", letter.upper(), page_num, len(links))

            # Check for next page
            next_href = AlphaPageParser.parse_next_page(html, BASE_URL)
            if next_href and next_href != current_url:
                current_url = next_href
                page_num += 1
                random_delay()
            else:
                current_url = None

        self.progress.state['total_drugs_found'] += len(all_links)
        return all_links

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with retry logic and Cloudflare handling."""
        try:
            return self._fetch_with_retry(url)
        except Exception as e:
            logger.error("Failed to fetch %s after retries: %s", url, e)
            return None

    @retry_on_failure(max_retries=3, exceptions=(Exception,))
    def _fetch_with_retry(self, url: str) -> str:
        """Fetch a single page (wrapped with retry decorator)."""
        return self.browser_mgr.navigate(self.page, url, wait_for_cf=CLOUDFLARE_WAIT)

    def _scrape_drug_detail(self, name: str, url: str) -> Optional[DrugInfo]:
        """Scrape a single drug's detail page and its side effects page."""
        try:
            # 1. Fetch main detail page
            html = self._fetch_page(url)
            if not html:
                return None

            data = DrugDetailParser.parse(html, url)

            # 2. Try to fetch side effects page
            drug_slug = self._extract_slug(url)
            if drug_slug:
                sfx_url = SIDE_EFFECTS_URL_TEMPLATE.format(drug_slug=drug_slug)
                try:
                    random_delay(min_sec=1.0, max_sec=3.0)
                    sfx_html = self._fetch_page(sfx_url)
                    if sfx_html:
                        data['side_effects'] = SideEffectsParser.parse(sfx_html)
                except Exception as e:
                    logger.debug("Side effects page not available for %s: %s", name, e)

            return DrugInfo(**data)

        except Exception as e:
            logger.error("Error scraping %s: %s", url, e)
            return None

    @staticmethod
    def _extract_slug(url: str) -> Optional[str]:
        """
        Extract drug slug from URL for constructing /sfx/ URL.
        e.g., "https://www.drugs.com/acetaminophen.html" -> "acetaminophen"
        e.g., "https://www.drugs.com/cdi/acetaminophen.html" -> "acetaminophen"
        """
        match = re.search(r'/([^/]+)\.html$', url)
        if match:
            return match.group(1)
        return None
