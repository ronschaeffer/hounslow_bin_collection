"""
Browser-based waste collection data retrieval using Playwright.

This module uses browser automation to access the Hounslow Council website
and retrieve bin collection dates, bypassing API protection mechanisms.
"""

import json
import logging
from datetime import datetime
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

logger = logging.getLogger(__name__)


class BrowserWasteCollector:
    """Browser automation-based waste collection data retriever."""

    BASE_URL = "https://my.hounslow.gov.uk"
    FORM_URL = f"{BASE_URL}/service/Waste_and_recycling_collections"

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Initialize the browser collector.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Timeout for page operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_browser()

    def start_browser(self) -> None:
        """Start the browser and create a new page."""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        logger.info("Browser started successfully")

    def close_browser(self) -> None:
        """Close the browser and cleanup resources."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        logger.info("Browser closed")

    def fetch_collection_data(
        self, postcode: str, address_hint: str | None = None
    ) -> dict[str, Any]:
        """Fetch waste collection data for a given postcode and optionally a specific address.

        Args:
            postcode: The postcode to search for
            address_hint: Optional specific address to look for in the dropdown

        Returns:
            Dictionary containing collection schedule data

        Raises:
            Exception: If data retrieval fails
        """
        if not self.page:
            raise RuntimeError(
                "Browser not started. Use as context manager or call start_browser()"
            )

        logger.info(f"Fetching collection data for postcode: {postcode}")
        if address_hint:
            logger.info(f"Looking for address: {address_hint}")

        try:
            # Navigate to the form
            logger.debug(f"Navigating to: {self.FORM_URL}")
            self.page.goto(self.FORM_URL)
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(3000)

            # Find and access the iframe
            iframe_element = self.page.query_selector('iframe[id="fillform-frame-1"]')
            if not iframe_element:
                raise Exception("Form iframe not found on the page")

            iframe_frame = iframe_element.content_frame()
            if not iframe_frame:
                raise Exception("Could not access iframe content")

            logger.debug("Successfully accessed iframe content")
            iframe_frame.wait_for_load_state("networkidle")

            # Dismiss cookie dialog if present
            cookie_close = self.page.query_selector('button:has-text("Close")')
            if cookie_close and cookie_close.is_visible():
                logger.debug("Dismissing cookie dialog")
                cookie_close.click()
                self.page.wait_for_timeout(1000)

            # Click on "Your address" tab
            address_tab = iframe_frame.query_selector('text="Your address"')
            if not address_tab:
                raise Exception("Could not find 'Your address' tab")

            logger.debug("Clicking on 'Your address' tab")
            address_tab.click()
            iframe_frame.wait_for_timeout(2000)

            # Find the postcode input
            postcode_input = iframe_frame.query_selector("#searchPostcode")
            if not postcode_input:
                raise Exception("Postcode input field not found")

            # Enter postcode
            logger.debug(f"Entering postcode: {postcode}")
            postcode_input.fill("")  # Clear first
            postcode_input.fill(postcode)

            # Trigger address lookup by pressing Enter (this is what works)
            logger.debug("Triggering address lookup with Enter key")
            postcode_input.press("Enter")
            iframe_frame.wait_for_timeout(4000)  # Extended wait for lookup

            # Check address dropdown
            address_dropdown = iframe_frame.query_selector("#selectedAddress")
            if not address_dropdown:
                raise Exception("Address dropdown not found")

            # Check dropdown options
            options = address_dropdown.query_selector_all("option")
            if len(options) <= 1:
                raise Exception(f"No addresses found for postcode {postcode}")

            logger.debug(f"Found {len(options)} address options")

            # Select address
            selected_option = None
            selected_value = None
            if address_hint:
                # Look for specific address
                for option in options[1:]:  # Skip first option (usually placeholder)
                    option_text = option.text_content() or ""
                    option_value = option.get_attribute("value")
                    if address_hint.lower() in option_text.lower():
                        selected_option = option
                        selected_value = option_value
                        logger.debug(f"Found matching address: {option_text}")
                        break

            if not selected_option:
                # Select the first real option
                selected_option = options[1] if len(options) > 1 else None
                selected_value = (
                    selected_option.get_attribute("value") if selected_option else None
                )

            if not selected_option or not selected_value:
                raise Exception("No valid address option found")

            # Select the address using JavaScript (since dropdown may not be visible)
            option_text = selected_option.text_content() or ""
            logger.debug(f"Selecting address: {option_text}")

            result = iframe_frame.evaluate(f"""
                () => {{
                    const dropdown = document.getElementById('selectedAddress');
                    if (dropdown) {{
                        dropdown.value = '{selected_value}';
                        dropdown.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'Address selected successfully';
                    }}
                    return 'Address selection failed';
                }}
            """)
            logger.debug(f"Address selection result: {result}")

            iframe_frame.wait_for_timeout(2000)

            # Get the UPRN that was populated
            uprn_field = iframe_frame.query_selector("#addressUPRN")
            uprn_value = (
                uprn_field.get_attribute("value") if uprn_field else selected_value
            )
            logger.debug(f"UPRN populated: {uprn_value}")

            # Look for Next/Continue button and click it
            next_buttons = iframe_frame.query_selector_all(
                'button:has-text("Next"), button:has-text("Continue"), button:has-text("Submit")'
            )

            next_clicked = False
            for btn in next_buttons:
                if btn.is_visible():
                    btn_text = btn.text_content() or ""
                    logger.debug(f"Clicking button: {btn_text}")
                    btn.click()
                    iframe_frame.wait_for_timeout(5000)  # Extended wait for loading
                    next_clicked = True
                    break

            if not next_clicked:
                logger.warning(
                    "No next button found, trying to extract data from current page"
                )

            # Wait additional time for collection data to load
            iframe_frame.wait_for_timeout(8000)

            # Extract collection data from the current page
            collection_data = self._extract_collection_data_from_iframe(
                iframe_frame, postcode, option_text, uprn_value or selected_value or ""
            )

            logger.info("Successfully retrieved collection data")
            return collection_data

        except Exception as e:
            logger.error(f"Failed to fetch collection data: {e}")
            # Take a screenshot for debugging
            try:
                screenshot_path = f"/tmp/hounslow_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.page.screenshot(path=screenshot_path)
                logger.info(f"Error screenshot saved to: {screenshot_path}")
            except Exception:
                pass
            raise

    def _extract_collection_data_from_iframe(
        self, iframe_frame, postcode: str, address: str, uprn: str
    ) -> dict[str, Any]:
        """Extract collection data from the iframe results page.

        Args:
            iframe_frame: The iframe frame object
            postcode: The postcode that was searched
            address: The selected address
            uprn: The UPRN value

        Returns:
            Dictionary containing extracted collection information
        """
        logger.debug("Extracting collection data from iframe results")

        # Initialize collection info
        collection_info = {
            "postcode": postcode,
            "address": address,
            "uprn": uprn,
            "collections": [],
            "extracted_at": datetime.now().isoformat(),
            "method": "browser_automation_iframe",
            "data_warning": "Collection dates may vary due to holidays and service changes. Only rely on specific dates provided by the council system.",
        }

        # Get the current page content
        page_content = iframe_frame.evaluate("() => document.body.innerText") or ""

        # Look for collection-related content
        collection_keywords = [
            "collection",
            "recycling",
            "refuse",
            "general waste",
            "garden waste",
            "food waste",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "next collection",
            "collection day",
            "bin day",
        ]

        # Check if we have collection information
        has_collection_info = any(
            keyword in page_content.lower() for keyword in collection_keywords
        )

        if has_collection_info:
            logger.debug("Found collection-related content")

            # Extract collection information by patterns
            import re

            lines = page_content.split("\n")
            collection_lines = []

            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if any(keyword in line_lower for keyword in collection_keywords):
                    # Include context around collection info
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context = [
                        line.strip() for line in lines[start:end] if line.strip()
                    ]
                    collection_lines.extend(context)

            # Remove duplicates while preserving order
            seen = set()
            unique_lines = []
            for line in collection_lines:
                if line and line not in seen:
                    seen.add(line)
                    unique_lines.append(line)

            # Try to extract structured collection data
            collections = []

            # Pattern 1: Look for day names with collection types
            day_pattern = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
            waste_pattern = r"(recycling|refuse|general|garden|food|waste|bin)"

            for line in unique_lines:
                line_lower = line.lower()

                # Find days
                day_matches = re.findall(day_pattern, line_lower)
                waste_matches = re.findall(waste_pattern, line_lower)

                if day_matches or waste_matches:
                    collections.append(
                        {
                            "text": line,
                            "days": day_matches,
                            "waste_types": waste_matches,
                        }
                    )

            # Pattern 2: Look for date patterns
            date_patterns = [
                r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",  # DD/MM/YYYY
                r"\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b",  # YYYY/MM/DD
                r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b",  # Month names
            ]

            dates_found = []
            for pattern in date_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                dates_found.extend(matches)

            if dates_found:
                collections.append(
                    {
                        "type": "dates",
                        "dates": dates_found,
                        "context": "Extracted date patterns",
                    }
                )

            collection_info["collections"] = collections
            collection_info["raw_lines"] = unique_lines[:20]  # First 20 relevant lines

        else:
            logger.warning("No collection information found in page content")
            # Store first part of content for debugging
            collection_info["debug_content"] = page_content[:500]

        # Store raw content summary
        collection_info["content_summary"] = {
            "total_length": len(page_content),
            "line_count": len(page_content.split("\n")),
            "has_collection_keywords": has_collection_info,
            "preview": page_content[:200] + "..."
            if len(page_content) > 200
            else page_content,
        }

        logger.debug(
            f"Extracted collection data with {len(collection_info.get('collections', []))} collection entries"
        )
        return collection_info
        """Extract collection data from the results page.

        Returns:
            Dictionary containing extracted collection information
        """
        logger.debug("Extracting collection data from results page")

        # Look for collection information on the page
        collection_info = {
            "uprn": None,
            "address": None,
            "collections": [],
            "extracted_at": datetime.now().isoformat(),
            "method": "browser_automation",
        }

        # Try to extract address information
        address_selectors = [
            ".address",
            ".property-address",
            '[class*="address"]',
            "h1, h2, h3",
            ".result-header",
        ]

        for selector in address_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    text = element.text_content()
                    if text:
                        text = text.strip()
                        if text and len(text) > 5:  # Basic validation
                            collection_info["address"] = text
                            logger.debug(f"Found address: {text}")
                            break
            except Exception:
                continue

        # Extract collection dates
        date_patterns = [
            r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",  # DD/MM/YYYY, DD-MM-YYYY, etc.
            r"\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b",  # YYYY/MM/DD, etc.
            r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",  # Day names
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b",  # Month names
        ]

        # Look for collection information in various containers
        content_selectors = [
            ".collection-info",
            ".bin-collection",
            ".results",
            ".content",
            "main",
            "body",
        ]

        page_content = ""
        for selector in content_selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    page_content = element.text_content()
                    break
            except Exception:
                continue

        if not page_content and self.page:
            page_content = self.page.evaluate("() => document.body.textContent") or ""

        # Ensure page_content is a string
        if not page_content:
            page_content = ""  # Look for specific collection types
        collection_types = ["General Waste", "Recycling", "Garden Waste", "Food Waste"]

        for collection_type in collection_types:
            # Try to find dates associated with this collection type
            lines = page_content.split("\n")
            for i, line in enumerate(lines):
                if collection_type.lower() in line.lower():
                    # Look in surrounding lines for dates
                    context_lines = lines[max(0, i - 2) : i + 3]
                    context_text = " ".join(context_lines)

                    import re

                    for pattern in date_patterns:
                        matches = re.findall(pattern, context_text, re.IGNORECASE)
                        if matches:
                            collection_info["collections"].append(
                                {
                                    "type": collection_type,
                                    "dates": matches,
                                    "context": context_text.strip(),
                                }
                            )
                            break

        # If no specific collections found, extract all dates from page
        if not collection_info["collections"]:
            import re

            all_dates = []
            for pattern in date_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                all_dates.extend(matches)

            if all_dates:
                collection_info["collections"].append(
                    {
                        "type": "Unknown",
                        "dates": all_dates,
                        "context": "Extracted from full page content",
                    }
                )

        # Store raw page content for debugging
        collection_info["raw_content"] = page_content[:1000]  # First 1000 chars

        logger.debug(
            f"Extracted {len(collection_info['collections'])} collection entries"
        )
        return collection_info

    def get_page_info(self) -> dict[str, Any]:
        """Get current page information for debugging.

        Returns:
            Dictionary with page title, URL, and content summary
        """
        if not self.page:
            return {"error": "No page loaded"}

        return {
            "title": self.page.title(),
            "url": self.page.url,
            "content_length": len(self.page.content()),
            "input_count": len(self.page.query_selector_all("input")),
            "button_count": len(self.page.query_selector_all("button")),
            "form_count": len(self.page.query_selector_all("form")),
        }


def fetch_collection_data_browser(
    postcode: str, address_hint: str | None = None, headless: bool = True
) -> dict[str, Any]:
    """Convenience function to fetch collection data using browser automation.

    Args:
        postcode: The postcode to search for
        address_hint: Optional specific address to look for in the dropdown
        headless: Whether to run browser in headless mode

    Returns:
        Dictionary containing collection schedule data
    """
    with BrowserWasteCollector(headless=headless) as collector:
        return collector.fetch_collection_data(postcode, address_hint)


if __name__ == "__main__":
    # Test the browser collector with configurable address
    import sys

    if len(sys.argv) > 1:
        test_postcode = sys.argv[1]
    else:
        test_postcode = "TW3 3EB"  # Hounslow Council's own postcode

    test_address = "7 Bath Rd" if len(sys.argv) <= 2 else sys.argv[2]

    print(f"Testing browser collection for postcode: {test_postcode}")
    print(f"Looking for address: {test_address}")
    if len(sys.argv) <= 2:
        print("(Using Hounslow Council's own address as default)")

    try:
        result = fetch_collection_data_browser(
            test_postcode, test_address, headless=True
        )
        print("Collection data retrieved:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
