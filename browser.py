"""
Browser management module using Patchright for Cloudflare bypass.

Patchright patches Playwright to avoid the Runtime.enable CDP leak
that Cloudflare uses for bot detection. It executes JavaScript in
isolated ExecutionContexts instead.
"""
import time
import logging

from patchright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages a persistent Patchright browser context for Cloudflare bypass."""

    def __init__(self, headless: bool = True, user_data_dir: str = "/tmp/drugs_scraper_profile"):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self._playwright = None
        self._context = None

    def start(self):
        """Launch browser with stealth configuration."""
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            channel="chrome",          # Real Chrome, not Chromium
            headless=self.headless,
            no_viewport=True,          # Use native resolution
            # Do NOT set custom user_agent - Patchright warns against this
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        logger.info("Browser started (headless=%s)", self.headless)
        return self._context

    def new_page(self):
        """Create a new page in the existing context."""
        if not self._context:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._context.new_page()

    def navigate(self, page, url: str, wait_for_cf: float = 8.0) -> str:
        """
        Navigate to URL and handle potential Cloudflare challenge.
        Returns the page HTML source after the page loads.
        """
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        self._wait_for_cloudflare(page, wait_for_cf)
        return page.content()

    def _wait_for_cloudflare(self, page, max_wait: float):
        """
        Detect and wait for Cloudflare challenge page to resolve.
        Checks page title/content for Cloudflare indicators and waits
        until they disappear or timeout is reached.
        """
        cf_indicators = [
            "just a moment",
            "checking your browser",
            "cf-browser-verification",
            "cloudflare",
        ]

        start = time.time()
        while time.time() - start < max_wait:
            title = page.title().lower()
            # Quick check on title first
            if not any(indicator in title for indicator in cf_indicators):
                # Double-check body content for edge cases
                try:
                    body_text = page.evaluate(
                        "() => document.body ? document.body.innerText.substring(0, 500).toLowerCase() : ''"
                    )
                except Exception:
                    body_text = ""

                if not any(indicator in body_text for indicator in cf_indicators):
                    logger.debug("Cloudflare challenge cleared (or not present)")
                    return

            time.sleep(1.0)
            logger.debug("Waiting for Cloudflare challenge... (%.1fs)", time.time() - start)

        logger.warning("Cloudflare wait timeout after %.1fs", max_wait)

    def close(self):
        """Shut down browser and playwright."""
        try:
            if self._context:
                self._context.close()
        except Exception as e:
            logger.debug("Error closing context: %s", e)
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.debug("Error stopping playwright: %s", e)
        logger.info("Browser closed")
