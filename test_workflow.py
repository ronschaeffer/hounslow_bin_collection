#!/usr/bin/env python3
"""
Test the complete postcode workflow for Hounslow Council waste collection.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def test_complete_workflow():
    """Test the complete workflow from postcode to collection information."""
    with BrowserWasteCollector(headless=True) as collector:
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        print(f"Navigating to: {collector.FORM_URL}")
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
            cookie_close.click()
            page.wait_for_timeout(1000)

        # Click address tab
        address_tab = iframe_frame.query_selector('text="Your address"')
        address_tab.click()
        iframe_frame.wait_for_timeout(2000)

        print("=== STARTING POSTCODE WORKFLOW ===")

        # Find the postcode input
        postcode_input = iframe_frame.query_selector("#searchPostcode")
        if not postcode_input:
            print("Postcode input not found!")
            return

        # Test with a real Hounslow postcode
        test_postcode = "TW7 7HX"  # Valid Hounslow postcode
        print(f"Entering postcode: {test_postcode}")

        # Fill postcode field
        postcode_input.fill(test_postcode)

        # Try triggering different events that might cause address lookup
        print("Triggering search events...")

        # Method 1: Tab out of field
        postcode_input.press("Tab")
        iframe_frame.wait_for_timeout(2000)

        # Check if address dropdown appeared
        address_dropdown = iframe_frame.query_selector("#selectedAddress")
        if address_dropdown and address_dropdown.is_visible():
            print("✅ Address dropdown became visible after Tab!")
        else:
            print("Address dropdown not visible after Tab, trying Enter...")

            # Method 2: Press Enter
            postcode_input.press("Enter")
            iframe_frame.wait_for_timeout(3000)

            if address_dropdown and address_dropdown.is_visible():
                print("✅ Address dropdown became visible after Enter!")
            else:
                print("Address dropdown not visible after Enter, trying blur event...")

                # Method 3: Click elsewhere to trigger blur
                postcode_input.evaluate("element => element.blur()")
                iframe_frame.wait_for_timeout(3000)

                if address_dropdown and address_dropdown.is_visible():
                    print("✅ Address dropdown became visible after blur!")
                else:
                    # Method 4: Check if there's a specific search function
                    print("Trying to find and call search function...")
                    search_result = iframe_frame.evaluate("""
                        () => {
                            // Look for common search function names
                            if (window.searchAddress) {
                                window.searchAddress();
                                return 'Called searchAddress()';
                            }
                            if (window.lookupAddress) {
                                window.lookupAddress();
                                return 'Called lookupAddress()';
                            }
                            if (window.postcodeLookup) {
                                window.postcodeLookup();
                                return 'Called postcodeLookup()';
                            }
                            // Try to trigger change event
                            const input = document.getElementById('searchPostcode');
                            if (input) {
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                return 'Triggered change/input events';
                            }
                            return 'No search function found';
                        }
                    """)
                    print(f"Search function result: {search_result}")
                    iframe_frame.wait_for_timeout(3000)

        # Take screenshot
        screenshot_path = "/tmp/hounslow_postcode_entered.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to: {screenshot_path}")

        # Check address dropdown status
        address_dropdown = iframe_frame.query_selector("#selectedAddress")
        if address_dropdown:
            is_visible = address_dropdown.is_visible()
            options = address_dropdown.query_selector_all("option")
            print(
                f"\nAddress dropdown status: visible={is_visible}, options={len(options)}"
            )

            if len(options) > 1:  # More than just placeholder
                print("Available addresses:")
                for i, option in enumerate(options[:10]):
                    value = option.get_attribute("value")
                    text_content = option.text_content()
                    text = text_content.strip() if text_content else ""
                    print(f"  {i}: value='{value}', text='{text}'")

                # Select the first real address
                real_options = [
                    opt
                    for opt in options
                    if opt.get_attribute("value") and opt.get_attribute("value").strip()
                ]
                if real_options:
                    selected_option = real_options[0]
                    selected_value = selected_option.get_attribute("value")
                    selected_text = selected_option.text_content()

                    print(f"\nSelecting address: {selected_text}")
                    address_dropdown.select_option(value=selected_value)
                    iframe_frame.wait_for_timeout(2000)

                    # Take screenshot after address selection
                    screenshot_path2 = "/tmp/hounslow_address_selected.png"
                    page.screenshot(path=screenshot_path2, full_page=True)
                    print(
                        f"Screenshot after address selection saved to: {screenshot_path2}"
                    )

                    # Check if UPRN was populated
                    uprn_field = iframe_frame.query_selector("#addressUPRN")
                    if uprn_field:
                        uprn_value = uprn_field.get_attribute("value")
                        print(f"UPRN populated: {uprn_value}")

                    # Look for Next button or continue workflow
                    next_buttons = iframe_frame.query_selector_all(
                        'button:has-text("Next"), button:has-text("Continue"), button:has-text("Submit")'
                    )
                    for btn in next_buttons:
                        if btn.is_visible():
                            btn_text = btn.text_content()
                            print(f"Found next button: '{btn_text}', clicking...")
                            btn.click()
                            iframe_frame.wait_for_timeout(3000)
                            break

                    # Check for collection information
                    final_content = iframe_frame.evaluate(
                        "() => document.body.innerText"
                    )

                    # Look for collection-related content
                    collection_keywords = [
                        "collection",
                        "recycling",
                        "refuse",
                        "general waste",
                        "garden waste",
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "next collection",
                    ]

                    found_collection_info = False
                    for keyword in collection_keywords:
                        if keyword in final_content.lower():
                            found_collection_info = True
                            break

                    if found_collection_info:
                        print("\n=== COLLECTION INFORMATION FOUND ===")

                        # Extract collection dates/info
                        lines = final_content.split("\n")
                        collection_lines = []

                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            if any(
                                keyword in line_lower for keyword in collection_keywords
                            ):
                                # Include context around collection info
                                start = max(0, i - 1)
                                end = min(len(lines), i + 2)
                                context = lines[start:end]
                                collection_lines.extend(context)

                        # Remove duplicates while preserving order
                        seen = set()
                        unique_lines = []
                        for line in collection_lines:
                            if line.strip() and line not in seen:
                                seen.add(line)
                                unique_lines.append(line)

                        print("Collection information extracted:")
                        for line in unique_lines[:20]:  # Limit output
                            print(f"  {line.strip()}")

                        # Take final screenshot
                        screenshot_path3 = "/tmp/hounslow_collection_info.png"
                        page.screenshot(path=screenshot_path3, full_page=True)
                        print(f"Final screenshot saved to: {screenshot_path3}")

                        return {
                            "success": True,
                            "uprn": uprn_value if "uprn_value" in locals() else None,
                            "postcode": test_postcode,
                            "collection_info": unique_lines,
                            "screenshots": [
                                screenshot_path,
                                screenshot_path2,
                                screenshot_path3,
                            ],
                        }
                    else:
                        print("No collection information found in final content")
                        print(f"Content preview: {final_content[:500]}")
            else:
                print("No addresses found for postcode")
        else:
            print("Address dropdown not found")

        return {
            "success": False,
            "error": "Could not complete workflow",
            "postcode": test_postcode,
        }


if __name__ == "__main__":
    result = test_complete_workflow()
    print(f"\nFinal result: {result}")
