#!/usr/bin/env python3
"""
Test the working postcode lookup to select address and get collection data.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def test_working_collection():
    """Test the complete workflow now that we know how it works."""
    with BrowserWasteCollector(headless=True) as collector:
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        try:
            print("=== WORKING HOUNSLOW COLLECTION TEST ===")
            print("Navigating to form...")

            page.goto(collector.FORM_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # Access iframe
            iframe_element = page.query_selector('iframe[id="fillform-frame-1"]')
            iframe_frame = iframe_element.content_frame()
            iframe_frame.wait_for_load_state("networkidle")

            # Dismiss cookie dialog
            cookie_close = page.query_selector('button:has-text("Close")')
            if cookie_close and cookie_close.is_visible():
                print("Dismissing cookie dialog...")
                cookie_close.click()
                page.wait_for_timeout(1000)

            # Click address tab
            address_tab = iframe_frame.query_selector('text="Your address"')
            print("Clicking 'Your address' tab...")
            address_tab.click()
            iframe_frame.wait_for_timeout(2000)

            # Enter postcode
            postcode_input = iframe_frame.query_selector("#searchPostcode")
            test_postcode = "TW7 7HX"
            print(f"Entering postcode: {test_postcode}")

            postcode_input.fill("")
            postcode_input.fill(test_postcode)
            postcode_input.press("Enter")  # This triggers the lookup
            iframe_frame.wait_for_timeout(4000)  # Wait for lookup

            # Check dropdown contents
            address_dropdown = iframe_frame.query_selector("#selectedAddress")
            if address_dropdown:
                options = address_dropdown.query_selector_all("option")
                print(f"Found {len(options)} address options:")

                target_address = "136, Worple Road"
                selected_uprn = None

                for i, option in enumerate(options):
                    value = option.get_attribute("value")
                    text = option.text_content() or ""
                    print(f"  {i}: {value} -> {text.strip()}")

                    # Look for our target address
                    if target_address in text:
                        selected_uprn = value
                        print(f"*** Found target address: {text.strip()}")

                # If we didn't find 136, let's pick 132 (close enough for testing)
                if not selected_uprn:
                    print(
                        f"Target address '{target_address}' not found. Using first valid address..."
                    )
                    for option in options[1:]:  # Skip the placeholder
                        value = option.get_attribute("value")
                        if value:
                            selected_uprn = value
                            text = option.text_content() or ""
                            print(f"Selected: {text.strip()}")
                            break

                if selected_uprn:
                    print(f"Selecting UPRN: {selected_uprn}")

                    # Select the address - try both methods
                    try:
                        address_dropdown.select_option(value=selected_uprn)
                        print("Successfully selected address using select_option")
                    except Exception as e:
                        print(f"select_option failed: {e}")
                        # Try JavaScript selection as fallback
                        result = iframe_frame.evaluate(f"""
                            () => {{
                                const dropdown = document.getElementById('selectedAddress');
                                if (dropdown) {{
                                    dropdown.value = '{selected_uprn}';
                                    dropdown.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return 'JS selection successful';
                                }}
                                return 'JS selection failed';
                            }}
                        """)
                        print(f"JavaScript selection result: {result}")

                    iframe_frame.wait_for_timeout(2000)

                    # Continue to next step or look for collection data
                    print("Looking for collection information...")

                    # Check if data appears automatically or if we need to proceed
                    collection_info = iframe_frame.evaluate("""
                        () => {
                            const text = document.body.innerText;
                            const lines = text.split('\\n');
                            const relevant = lines.filter(line =>
                                line.includes('collection') ||
                                line.includes('bin') ||
                                line.includes('waste') ||
                                line.includes('recycling') ||
                                line.includes('Monday') ||
                                line.includes('Tuesday') ||
                                line.includes('Wednesday') ||
                                line.includes('Thursday') ||
                                line.includes('Friday')
                            );
                            return relevant.length > 0 ? relevant : ['No collection info found yet'];
                        }
                    """)

                    print("Collection information found:")
                    for info in collection_info[:10]:  # Show first 10 relevant lines
                        print(f"  - {info}")

                    # Look for Next/Continue button
                    next_buttons = iframe_frame.query_selector_all(
                        'button:has-text("Next"), button:has-text("Continue"), button:has-text("Submit")'
                    )
                    if next_buttons:
                        for btn in next_buttons:
                            if btn.is_visible():
                                btn_text = btn.text_content()
                                print(f"Clicking '{btn_text}' button...")
                                btn.click()
                                iframe_frame.wait_for_timeout(3000)
                                break

                    # Take final screenshot
                    page.screenshot(
                        path="/tmp/hounslow_final_result.png", full_page=True
                    )
                    print("Final screenshot saved: /tmp/hounslow_final_result.png")

                    # Get final collection data
                    final_content = iframe_frame.evaluate(
                        "() => document.body.innerText"
                    )
                    print("\nFinal page content (looking for collection details):")

                    # Extract collection-related information
                    lines = final_content.split("\n")
                    collection_lines = [
                        line.strip()
                        for line in lines
                        if line.strip()
                        and any(
                            keyword in line.lower()
                            for keyword in [
                                "collection",
                                "bin",
                                "waste",
                                "recycling",
                                "refuse",
                                "garden",
                                "food",
                                "monday",
                                "tuesday",
                                "wednesday",
                                "thursday",
                                "friday",
                                "saturday",
                                "sunday",
                                "weekly",
                                "fortnightly",
                                "next",
                                "due",
                            ]
                        )
                    ]

                    if collection_lines:
                        print("Collection information extracted:")
                        for line in collection_lines[:15]:
                            print(f"  {line}")
                    else:
                        print("No specific collection information found. Full content:")
                        print(final_content[-1000:])  # Last 1000 chars

                else:
                    print("No valid UPRN found to select")
            else:
                print("Address dropdown not found")

        except Exception as e:
            print(f"Error in working collection test: {e}")
            page.screenshot(path="/tmp/hounslow_error_working.png", full_page=True)
            print("Error screenshot saved: /tmp/hounslow_error_working.png")


if __name__ == "__main__":
    test_working_collection()
