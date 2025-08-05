"""
Fixed implementation for Hounslow Council waste collection schedule.

This replaces the broken implementation in the HACS waste collection schedule
by using browser automation to bypass API security measures.

Based on the working browser automation from hounslow_bin_collection project.
Now uses postcode + address_hint (street address) parameters instead of UPRN.
"""

from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from playwright.sync_api import sync_playwright
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Hounslow"
DESCRIPTION = "Source for London Borough of Hounslow."
URL = "https://hounslow.gov.uk"
TEST_CASES = {
    "Hounslow High Street": {"postcode": "TW3 1ES", "address_hint": "High Street"},
    "Bath Road": {"postcode": "TW5 9QE", "address_hint": "Bath Road"},
    "Postcode only": {"postcode": "TW4 6JP"},
}

ICON_MAP = {
    "Black": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "Food": "mdi:food",
}

# The new URL that actually works with browser automation
FORM_URL = "https://my.hounslow.gov.uk/service/Waste_and_recycling_collections"


class Source:
    def __init__(self, postcode: str, address_hint: str | None = None):
        """
        Initialize the Hounslow waste collection source.

        Args:
            postcode: The postcode to search for
            address_hint: Optional street address hint to help with matching
        """
        self._postcode: str = postcode
        self._address_hint: str | None = address_hint

    def fetch(self) -> list[Collection]:
        """
        Fetch waste collection data using browser automation.

        This method replaces the broken direct API calls with browser automation
        that can handle the security measures on the Hounslow website.
        """
        entries = []

        # Try browser automation first (most reliable)
        try:
            entries = self._fetch_with_browser_automation()
            if entries:
                return entries
        except Exception:
            # If browser automation fails, fall back to trying the old method
            # (though it will likely fail due to security measures)
            pass

        # Fallback to original method (likely to fail but worth trying)
        try:
            entries = self._fetch_original_method()
        except Exception:
            # If both methods fail, raise an informative error
            raise Exception(
                f"Unable to fetch waste collection data for postcode {self._postcode}. "
                "The Hounslow Council website may have security measures that prevent automated access. "
                "Try using a more recent version of this integration or check the postcode at: "
                "https://my.hounslow.gov.uk/service/Waste_and_recycling_collections"
            ) from None

        return entries

    def _fetch_with_browser_automation(self) -> list[Collection]:
        """
        Fetch data using browser automation (most reliable method).
        Based on the working implementation from hounslow_bin_collection project.
        """
        entries = []

        with sync_playwright() as playwright:
            # Use headless browser for server environments
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(30000)  # 30 seconds

            try:
                # Navigate to the form
                page.goto(FORM_URL)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)

                # Find and access the iframe
                iframe_element = page.query_selector('iframe[id="fillform-frame-1"]')
                if not iframe_element:
                    raise Exception("Form iframe not found on the page")

                iframe_frame = iframe_element.content_frame()
                if not iframe_frame:
                    raise Exception("Could not access iframe content")

                iframe_frame.wait_for_load_state("networkidle")

                # Dismiss cookie dialog if present
                cookie_close = page.query_selector('button:has-text("Close")')
                if cookie_close and cookie_close.is_visible():
                    cookie_close.click()
                    page.wait_for_timeout(1000)

                # Search by postcode and address hint
                success = self._search_by_postcode(iframe_frame, page)
                if success:
                    # Extract data from the results
                    entries = self._extract_collection_data(iframe_frame)

            finally:
                browser.close()

        return entries

    def _search_by_postcode(self, iframe_frame, page) -> bool:
        """
        Search for the address using postcode and select by address hint.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Click on "Your address" tab
            address_tab = iframe_frame.query_selector('text="Your address"')
            if not address_tab:
                return False

            address_tab.click()
            iframe_frame.wait_for_timeout(2000)

            # Find the postcode input
            postcode_input = iframe_frame.query_selector("#searchPostcode")
            if not postcode_input:
                return False

            # Enter postcode
            postcode_input.fill("")  # Clear first
            postcode_input.fill(self._postcode)

            # Trigger address lookup
            postcode_input.press("Enter")
            iframe_frame.wait_for_timeout(4000)

            # Check address dropdown
            address_dropdown = iframe_frame.query_selector("#selectedAddress")
            if not address_dropdown:
                return False

            # Check dropdown options
            options = address_dropdown.query_selector_all("option")
            if len(options) <= 1:
                return False

            # Look for the option that best matches our address hint
            selected_option = None
            selected_value = None

            if self._address_hint:
                # Try to find a matching address using the hint
                best_match_score = 0
                address_hint_lower = self._address_hint.lower()

                for option in options[1:]:  # Skip first option (usually placeholder)
                    option_value = option.get_attribute("value")
                    option_text = (option.text_content() or "").lower()

                    if option_value:
                        # Score the match based on how well the address hint matches
                        score = 0
                        for word in address_hint_lower.split():
                            if word in option_text:
                                score += len(word)

                        if score > best_match_score:
                            best_match_score = score
                            selected_option = option
                            selected_value = option_value

            # If no good match found with address hint, use first available option
            if not selected_option and len(options) > 1:
                selected_option = options[1]
                selected_value = selected_option.get_attribute("value")

            if not selected_option or not selected_value:
                return False

            # Select the address using JavaScript
            iframe_frame.evaluate(f"""
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

            iframe_frame.wait_for_timeout(2000)

            # Look for Next/Continue button and click it
            next_buttons = iframe_frame.query_selector_all(
                'button:has-text("Next"), button:has-text("Continue"), button:has-text("Submit")'
            )

            for btn in next_buttons:
                if btn.is_visible():
                    btn.click()
                    iframe_frame.wait_for_timeout(5000)
                    break

            return True

        except Exception:
            return False

    def _extract_collection_data(self, iframe_frame) -> list[Collection]:
        """
        Extract collection data from the iframe results page.
        """
        entries = []

        try:
            # Wait for data to load
            iframe_frame.wait_for_timeout(3000)

            # Get the current page content
            page_content = iframe_frame.evaluate("() => document.body.innerText") or ""

            # Look for collection information patterns
            lines = page_content.split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for date patterns and waste types
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "collection",
                        "recycling",
                        "refuse",
                        "general waste",
                        "garden waste",
                        "food waste",
                    ]
                ):
                    # Try to extract date and type information
                    date_match = self._extract_date_from_line(line)
                    waste_type = self._extract_waste_type_from_line(line)

                    if date_match and waste_type:
                        entries.append(
                            Collection(
                                date=date_match,
                                t=waste_type,
                                icon=ICON_MAP.get(
                                    waste_type.split(" ")[0], "mdi:trash-can"
                                ),
                            )
                        )

        except Exception:
            pass

        return entries

    def _extract_date_from_line(self, line: str):
        """
        Try to extract a date from a line of text.
        """
        import re

        # Try different date patterns
        date_patterns = [
            r"(\d{1,2} \w+ \d{4})",  # "25 Dec 2024"
            r"(\w+ \d{1,2} \w+ \d{4})",  # "Friday 25 Dec 2024"
        ]

        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    try:
                        return datetime.strptime(date_str, "%d %b %Y").date()
                    except ValueError:
                        return datetime.strptime(date_str, "%A %d %b %Y").date()
                except ValueError:
                    continue

        return None

    def _extract_waste_type_from_line(self, line: str) -> str:
        """
        Extract waste type from a line of text.
        """
        line_lower = line.lower()

        if "recycling" in line_lower:
            return "Recycling"
        elif "garden" in line_lower:
            return "Garden"
        elif "food" in line_lower:
            return "Food"
        elif "general" in line_lower or "refuse" in line_lower or "black" in line_lower:
            return "Black"
        else:
            return "General"

    def _fetch_original_method(self) -> list[Collection]:
        """
        Try the original API method (likely to fail due to security measures).

        This is kept as a fallback, but will probably not work due to
        anti-automation measures on the Hounslow website.
        """
        # Original broken URL - this is likely blocked now
        api_url = "https://www.hounslow.gov.uk/homepage/86/recycling_and_waste_collection_day_finder#collectionday"

        # We can't use UPRN anymore since we switched to postcode+address approach
        # This method is mainly here as a placeholder and will likely fail
        args = {
            "postcode": self._postcode,
        }

        r = requests.post(api_url, data=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        bin_cal_divs = soup.find_all("div", class_="bin_day_main_wrapper")
        entries = []

        for bin_cal_div in bin_cal_divs:
            # Extract the address information safely
            if isinstance(bin_cal_div, Tag):
                collection_info = bin_cal_div.find_all("h4")
                for info in collection_info:
                    if isinstance(info, Tag) and info.text:
                        date_splitted = info.text.strip().split("-")
                        date_str = (
                            date_splitted[1]
                            if len(date_splitted) > 1
                            else date_splitted[0]
                        ).strip()
                        try:
                            date = datetime.strptime(date_str, "%d %b %Y").date()
                        except ValueError:
                            try:
                                date = datetime.strptime(date_str, "%A %d %b %Y").date()
                            except ValueError:
                                continue

                        ul_element = info.find_next("ul", class_="list-group")
                        if ul_element and isinstance(ul_element, Tag):
                            bins = [
                                li.text.strip()
                                for li in ul_element.find_all("li")
                                if isinstance(li, Tag) and li.text
                            ]

                            for bin_name in bins:
                                entries.append(
                                    Collection(
                                        date=date,
                                        t=bin_name,
                                        icon=ICON_MAP.get(bin_name.split(" ")[0]),
                                    )
                                )

        return entries
