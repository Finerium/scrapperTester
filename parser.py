"""
HTML parsing module using BeautifulSoup.

drugs.com uses a "ddc-" prefix convention for CSS classes.
Each parser has multiple fallback selectors tried in order.

NOTE: Selectors are based on known drugs.com patterns. If the site
structure changes, update the selectors here -- no other file
needs to change.
"""
import re
import logging
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AlphaPageParser:
    """Parse alphabetical drug listing pages (/alpha/X.html)."""

    DRUG_LIST_SELECTORS = [
        "ul.ddc-list-column-2 li a",
        "ul.ddc-list-column-3 li a",
        "div.ddc-media-list a",
        "#content ul li a",
    ]

    NEXT_PAGE_SELECTORS = [
        "a.ddc-paging-item-next",
        "a[rel='next']",
    ]

    PAGINATION_SELECTORS = [
        "div.ddc-paging a",
        "nav.ddc-paging a",
        "div.paging a",
    ]

    # URL patterns to exclude (not individual drug pages)
    EXCLUDE_PATTERNS = [
        '/drug-class', '/alpha/', '/search', '/sfx/',
        '/interactions', '/support/', '/members',
        '/condition/', '/dosage/', '/pregnancy/',
        '/pro/', '/npc/', '/monograph/',
        '#',
    ]

    @classmethod
    def parse_drug_links(cls, html: str, base_url: str) -> List[Tuple[str, str]]:
        """Extract (drug_name, drug_url) tuples from an alpha listing page."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for selector in cls.DRUG_LIST_SELECTORS:
            elements = soup.select(selector)
            if elements:
                logger.debug("Matched selector: %s (%d links)", selector, len(elements))
                for el in elements:
                    href = el.get('href', '')
                    name = el.get_text(strip=True)
                    if href and name and cls._is_drug_url(href):
                        if href.startswith('/'):
                            href = base_url + href
                        links.append((name, href))
                break
        else:
            # Fallback: find all anchors in main content area
            logger.warning("No drug list selector matched; using broad fallback")
            content = soup.find('div', id='content') or soup.find('main') or soup
            for a in content.find_all('a', href=True):
                href = a['href']
                name = a.get_text(strip=True)
                if cls._is_drug_url(href) and name and len(name) > 1:
                    if href.startswith('/'):
                        href = base_url + href
                    links.append((name, href))

        return links

    @classmethod
    def _is_drug_url(cls, href: str) -> bool:
        """Filter to identify actual drug page URLs vs navigation links."""
        if not href or not href.endswith('.html'):
            return False
        return not any(pat in href for pat in cls.EXCLUDE_PATTERNS)

    @classmethod
    def parse_next_page(cls, html: str, base_url: str) -> Optional[str]:
        """Find the 'next page' URL if pagination exists."""
        soup = BeautifulSoup(html, 'html.parser')

        # Try explicit next-page selectors
        for selector in cls.NEXT_PAGE_SELECTORS:
            next_el = soup.select_one(selector)
            if next_el and next_el.get('href'):
                href = next_el['href']
                if href.startswith('/'):
                    href = base_url + href
                return href

        # Fallback: look for pagination with numbered links
        for selector in cls.PAGINATION_SELECTORS:
            paging_links = soup.select(selector)
            if paging_links:
                # Find active/current page, get the next link
                container = paging_links[0].parent
                if container:
                    active = container.find(class_=re.compile(r'active|current|ddc-active'))
                    if active:
                        next_sib = active.find_next_sibling('a')
                        if next_sib and next_sib.get('href'):
                            href = next_sib['href']
                            if href.startswith('/'):
                                href = base_url + href
                            return href

        return None


class DrugDetailParser:
    """Parse individual drug detail pages."""

    NAME_SELECTORS = [
        "h1.ddc-header-title",
        "h1",
    ]

    GENERIC_NAME_SELECTORS = [
        "p.drug-subtitle",
        "span.drug-subtitle",
        ".ddc-subtitle",
        "p.drug-generic-name",
    ]

    GENERIC_NAME_PATTERN = re.compile(
        r"(?:Generic\s+[Nn]ame|generic[:\s])\s*[:.]?\s*(.+)",
        re.IGNORECASE
    )

    DESCRIPTION_SELECTORS = [
        "div.ddc-media-content p",
        "div.contentBox p",
        "#content > p",
    ]

    DRUG_CLASS_TABLE_HEADER = re.compile(r"Drug\s+class", re.IGNORECASE)

    RATING_PATTERN = re.compile(r"(\d+\.?\d*)\s*/?\s*10")

    RATING_SELECTORS = [
        "div.ddc-rating-summary .ddc-rating-avg",
        "span.ddc-rating-avg",
        ".ratings-avg-number",
        "div[class*='rating'] span",
    ]

    @classmethod
    def parse(cls, html: str, url: str) -> dict:
        """Extract all drug information from a detail page."""
        soup = BeautifulSoup(html, 'html.parser')

        return {
            'name': cls._extract_name(soup),
            'generic_name': cls._extract_generic_name(soup),
            'url': url,
            'description': cls._extract_description(soup),
            'drug_class': cls._extract_drug_class(soup),
            'rating': cls._extract_rating(soup),
            'side_effects': [],
        }

    @classmethod
    def _extract_name(cls, soup: BeautifulSoup) -> str:
        for selector in cls.NAME_SELECTORS:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return "Unknown"

    @classmethod
    def _extract_generic_name(cls, soup: BeautifulSoup) -> Optional[str]:
        # Strategy 1: explicit generic name element
        for selector in cls.GENERIC_NAME_SELECTORS:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                match = cls.GENERIC_NAME_PATTERN.search(text)
                if match:
                    return match.group(1).strip()
                if text and 'brand' not in text.lower():
                    return text

        # Strategy 2: search for "Generic Name:" text pattern
        generic_label = soup.find(string=cls.GENERIC_NAME_PATTERN)
        if generic_label:
            match = cls.GENERIC_NAME_PATTERN.search(generic_label)
            if match:
                return match.group(1).strip()

        return None

    @classmethod
    def _extract_description(cls, soup: BeautifulSoup) -> Optional[str]:
        """Extract the first meaningful paragraph(s) of drug description."""
        # Try to find "What is [drug]?" section first
        what_is_heading = soup.find(
            ['h2', 'h3'],
            string=re.compile(r'What\s+is', re.IGNORECASE)
        )
        if what_is_heading:
            paragraphs = []
            sibling = what_is_heading.find_next_sibling()
            while sibling and sibling.name == 'p' and len(paragraphs) < 3:
                text = sibling.get_text(strip=True)
                if text:
                    paragraphs.append(text)
                sibling = sibling.find_next_sibling()
            if paragraphs:
                return ' '.join(paragraphs)

        # Fallback: use content selectors
        for selector in cls.DESCRIPTION_SELECTORS:
            elements = soup.select(selector)
            if elements:
                paragraphs = [
                    el.get_text(strip=True)
                    for el in elements[:3]
                    if el.get_text(strip=True)
                ]
                if paragraphs:
                    return ' '.join(paragraphs)

        return None

    @classmethod
    def _extract_drug_class(cls, soup: BeautifulSoup) -> Optional[str]:
        """Extract drug class from link or table."""
        # Strategy 1: link to /drug-class/
        drug_class_link = soup.select_one("a[href*='/drug-class']")
        if drug_class_link:
            return drug_class_link.get_text(strip=True)

        # Strategy 2: find "Drug class" in table rows
        for row in soup.find_all('tr'):
            header_cell = row.find(['th', 'td'])
            if header_cell and cls.DRUG_CLASS_TABLE_HEADER.search(header_cell.get_text()):
                value_cell = header_cell.find_next_sibling('td')
                if value_cell:
                    # Might contain a link
                    link = value_cell.find('a')
                    if link:
                        return link.get_text(strip=True)
                    return value_cell.get_text(strip=True)

        # Strategy 3: look for "Drug class" text pattern
        class_text = soup.find(string=re.compile(r'Drug\s+class', re.IGNORECASE))
        if class_text:
            parent = class_text.parent
            if parent:
                next_el = parent.find_next_sibling()
                if next_el:
                    return next_el.get_text(strip=True)

        return None

    @classmethod
    def _extract_rating(cls, soup: BeautifulSoup) -> Optional[float]:
        for selector in cls.RATING_SELECTORS:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                match = cls.RATING_PATTERN.search(text)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        return None


class SideEffectsParser:
    """Parse side effects from /sfx/ pages."""

    COMMON_SE_HEADING = re.compile(
        r"(?:common|more common|most common)\s+side\s+effects",
        re.IGNORECASE
    )

    SIDE_EFFECTS_LIST_SELECTORS = [
        "div.ddc-list-column-2 ul li",
        "div.ddc-list-column-1 ul li",
        "ul.ddc-list-unstyled li",
    ]

    @classmethod
    def parse(cls, html: str) -> List[str]:
        """Extract common side effects as a list of strings."""
        soup = BeautifulSoup(html, 'html.parser')
        side_effects = []

        # Strategy 1: find "common side effects" heading, grab the list after it
        heading = soup.find(
            ['h2', 'h3', 'h4'],
            string=cls.COMMON_SE_HEADING
        )
        if heading:
            sibling = heading.find_next_sibling()
            while sibling:
                if sibling.name == 'ul':
                    for li in sibling.find_all('li'):
                        text = li.get_text(strip=True)
                        if text:
                            side_effects.append(text)
                    break
                if sibling.name in ['h2', 'h3', 'h4']:
                    break  # New section
                sibling = sibling.find_next_sibling()

        if side_effects:
            return side_effects[:30]

        # Strategy 2: CSS selectors
        for selector in cls.SIDE_EFFECTS_LIST_SELECTORS:
            elements = soup.select(selector)
            if elements and len(elements) > 2:
                candidates = [
                    el.get_text(strip=True)
                    for el in elements
                    if el.get_text(strip=True) and len(el.get_text(strip=True)) < 100
                ]
                if len(candidates) > 2:
                    return candidates[:30]

        # Strategy 3: paragraph-based list
        se_section = soup.find(string=re.compile(r'side\s+effects', re.IGNORECASE))
        if se_section:
            parent = se_section.find_parent(['div', 'section'])
            if parent:
                bullets = parent.find_all('li')
                if bullets:
                    return [b.get_text(strip=True) for b in bullets[:30]]

        return []
