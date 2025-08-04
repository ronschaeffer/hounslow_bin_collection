#!/usr/bin/env python3
"""
Navigate through the Hounslow Council form wizard to find the postcode/address entry.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def debug_address_tab():
    """Navigate to the address tab and explore the form."""
    with BrowserWasteCollector(headless=True) as collector:
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        print(f"Navigating to: {collector.FORM_URL}")
        page.goto(collector.FORM_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Find and access the iframe
        iframe_element = page.query_selector('iframe[id="fillform-frame-1"]')
        if not iframe_element:
            print("Iframe not found!")
            return

        iframe_frame = iframe_element.content_frame()
        if not iframe_frame:
            print("Could not access iframe content!")
            return

        print("Successfully accessed iframe content!")
        iframe_frame.wait_for_load_state("networkidle")

        # First, check if there's a cookie dialog and dismiss it
        # Check in main page first
        cookie_close = page.query_selector('button:has-text("Close")')
        if cookie_close and cookie_close.is_visible():
            print("Dismissing cookie dialog...")
            cookie_close.click()
            page.wait_for_timeout(1000)

        # Also check for cookie dialog in iframe
        iframe_cookie_close = iframe_frame.query_selector('button:has-text("Close")')
        if iframe_cookie_close and iframe_cookie_close.is_visible():
            print("Dismissing iframe cookie dialog...")
            iframe_cookie_close.click()
            iframe_frame.wait_for_timeout(1000)

        # Click on "Your address" tab
        address_tab = iframe_frame.query_selector('text="Your address"')
        if not address_tab:
            print("Could not find 'Your address' tab!")
            return

        print("Clicking on 'Your address' tab...")
        address_tab.click()
        iframe_frame.wait_for_timeout(2000)  # Wait for tab content to load

        # Take screenshot after clicking address tab
        screenshot_path = "/tmp/hounslow_address_tab.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot after clicking address tab saved to: {screenshot_path}")

        # Now look for postcode inputs again
        postcode_selectors = [
            'input[name*="postcode" i]',
            'input[id*="postcode" i]',
            'input[placeholder*="postcode" i]',
            'input[placeholder*="post code" i]',
            'input[aria-label*="postcode" i]',
            'input[type="text"]',
        ]

        print("\nLooking for postcode inputs in address tab...")
        postcode_inputs = []
        for selector in postcode_selectors:
            elements = iframe_frame.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for elem in elements:
                    name = elem.get_attribute("name")
                    id_attr = elem.get_attribute("id")
                    placeholder = elem.get_attribute("placeholder")
                    input_type = elem.get_attribute("type")

                    # Check if element is visible
                    is_visible = elem.is_visible()

                    # Try to find associated label
                    label_text = ""
                    if id_attr:
                        label = iframe_frame.query_selector(f'label[for="{id_attr}"]')
                        if label:
                            label_text = label.text_content() or ""

                    print(
                        f"  - name={name}, id={id_attr}, type={input_type}, visible={is_visible}"
                    )
                    print(
                        f"    placeholder='{placeholder}', label='{label_text.strip()}'"
                    )

                    if is_visible:
                        postcode_inputs.append(elem)

        # Look for address dropdowns in the address tab
        selects = iframe_frame.query_selector_all("select")
        print(f"\nFound {len(selects)} select/dropdown elements in address tab:")

        visible_selects = []
        for i, select in enumerate(selects):
            name = select.get_attribute("name")
            id_attr = select.get_attribute("id")
            select_class = select.get_attribute("class")
            is_visible = select.is_visible()

            # Try to find associated label
            label_text = ""
            if id_attr:
                label = iframe_frame.query_selector(f'label[for="{id_attr}"]')
                if label:
                    label_text = label.text_content() or ""

            options = select.query_selector_all("option")
            print(f"Select {i}: name={name}, id={id_attr}, visible={is_visible}")
            print(f"  class={select_class}, label='{label_text.strip()}'")
            print(f"  Has {len(options)} options")

            if is_visible:
                visible_selects.append(select)
                if options:
                    for j, option in enumerate(options[:5]):
                        value = option.get_attribute("value")
                        text_content = option.text_content()
                        text = text_content.strip() if text_content else ""
                        print(f"    Option {j}: value='{value}', text='{text}'")
                    if len(options) > 5:
                        print(f"    ... and {len(options) - 5} more options")

        # Get current tab content
        tab_content = iframe_frame.evaluate("() => document.body.innerText")
        print("\nAddress tab content preview (first 1000 chars):")
        print(tab_content[:1000] + "..." if len(tab_content) > 1000 else tab_content)

        # If we found visible postcode inputs, test the workflow
        if postcode_inputs:
            print("\n=== TESTING POSTCODE WORKFLOW ===")
            test_postcode = "TW3 1ES"  # Hounslow postcode

            print(f"Found {len(postcode_inputs)} visible postcode input(s)")
            postcode_input = postcode_inputs[0]

            try:
                print(f"Filling postcode input with: {test_postcode}")
                postcode_input.fill(test_postcode)

                # Look for search/submit buttons
                search_selectors = [
                    'button:has-text("Search")',
                    'button:has-text("Find")',
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                ]

                search_button = None
                for selector in search_selectors:
                    btn = iframe_frame.query_selector(selector)
                    if btn and btn.is_visible():
                        search_button = btn
                        button_text = btn.text_content() or ""
                        print(f"Found search button: '{button_text.strip()}'")
                        break

                if search_button:
                    print("Clicking search button...")
                    search_button.click()
                    iframe_frame.wait_for_timeout(3000)  # Wait for response

                    # Check for new dropdowns
                    new_selects = iframe_frame.query_selector_all("select")
                    print(f"After postcode search: Found {len(new_selects)} dropdowns")

                    for select in new_selects:
                        if select.is_visible():
                            options = select.query_selector_all("option")
                            if len(options) > 1:  # More than just placeholder
                                name = select.get_attribute("name")
                                print(
                                    f"Dropdown '{name}' now has {len(options)} options:"
                                )
                                for j, option in enumerate(options[:10]):
                                    value = option.get_attribute("value")
                                    text_content = option.text_content()
                                    text = text_content.strip() if text_content else ""
                                    print(f"  {j}: value='{value}', text='{text}'")
                                if len(options) > 10:
                                    print(f"  ... and {len(options) - 10} more options")

                                # If this looks like addresses, try to select one
                                if (
                                    "address" in (name or "").lower()
                                    or len(options) > 5
                                ):
                                    print("This looks like an address dropdown!")
                                    # Select the first real option (skip placeholder)
                                    for option in options[1:]:
                                        option_value = option.get_attribute("value")
                                        if option_value and option_value.strip():
                                            print(
                                                f"Selecting address option: {option_value}"
                                            )
                                            select.select_option(value=option_value)
                                            iframe_frame.wait_for_timeout(2000)
                                            break

                    # Take screenshot after address selection
                    screenshot_path2 = "/tmp/hounslow_after_address_selection.png"
                    page.screenshot(path=screenshot_path2, full_page=True)
                    print(
                        f"Screenshot after address selection saved to: {screenshot_path2}"
                    )

                    # Look for next step or collection information
                    final_content = iframe_frame.evaluate(
                        "() => document.body.innerText"
                    )
                    if (
                        "collection" in final_content.lower()
                        or "bin" in final_content.lower()
                    ):
                        print("\n=== FOUND COLLECTION INFORMATION ===")
                        # Look for collection dates or schedule
                        collection_keywords = [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                            "recycling",
                            "general",
                            "garden",
                            "food waste",
                            "refuse",
                        ]

                        lines = final_content.split("\n")
                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            if any(
                                keyword in line_lower for keyword in collection_keywords
                            ):
                                # Print context around this line
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                print("Collection information found:")
                                for j in range(start, end):
                                    marker = ">>> " if j == i else "    "
                                    print(f"{marker}{lines[j].strip()}")
                                print()

                else:
                    print("No search button found after entering postcode")

            except Exception as e:
                print(f"Error during postcode workflow: {e}")

        else:
            print("No visible postcode inputs found in address tab")


if __name__ == "__main__":
    debug_address_tab()
