#!/usr/bin/env python3
"""
Debug script to explore the Hounslow Council iframe with the actual form.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def debug_iframe():
    """Debug the iframe that contains the actual form."""
    with BrowserWasteCollector(headless=True) as collector:
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        print(f"Navigating to: {collector.FORM_URL}")
        page.goto(collector.FORM_URL)
        page.wait_for_load_state("networkidle")

        # Wait a bit more for iframe to load
        page.wait_for_timeout(3000)

        # Find the iframe
        iframe_element = page.query_selector('iframe[id="fillform-frame-1"]')
        if not iframe_element:
            print("Iframe not found!")
            return

        # Get the iframe content
        iframe_frame = iframe_element.content_frame()
        if not iframe_frame:
            print("Could not access iframe content!")
            return

        print("Successfully accessed iframe content!")
        print(f"Iframe URL: {iframe_frame.url}")

        # Wait for iframe content to load
        iframe_frame.wait_for_load_state("networkidle")

        # Get page title from iframe
        iframe_title = iframe_frame.title()
        print(f"Iframe title: {iframe_title}")

        # Look for forms in iframe
        forms = iframe_frame.query_selector_all("form")
        print(f"\nFound {len(forms)} forms in iframe")

        for i, form in enumerate(forms):
            action = form.get_attribute("action")
            method = form.get_attribute("method")
            form_id = form.get_attribute("id")
            form_class = form.get_attribute("class")
            print(
                f"Form {i}: action={action}, method={method}, id={form_id}, class={form_class}"
            )

        # Look for postcode inputs
        postcode_selectors = [
            'input[name*="postcode" i]',
            'input[id*="postcode" i]',
            'input[placeholder*="postcode" i]',
            'input[placeholder*="post code" i]',
            'input[aria-label*="postcode" i]',
            'input[type="text"]',  # Fallback to any text input
        ]

        print("\nLooking for postcode inputs in iframe...")
        postcode_inputs = []
        for selector in postcode_selectors:
            elements = iframe_frame.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for elem in elements:
                    name = elem.get_attribute("name")
                    id_attr = elem.get_attribute("id")
                    placeholder = elem.get_attribute("placeholder")
                    label_text = ""
                    # Try to find associated label
                    if id_attr:
                        label = iframe_frame.query_selector(f'label[for="{id_attr}"]')
                        if label:
                            label_text = label.text_content()

                    print(
                        f"  - name={name}, id={id_attr}, placeholder={placeholder}, label='{label_text}'"
                    )
                    postcode_inputs.append(elem)

        # Look for address dropdowns
        selects = iframe_frame.query_selector_all("select")
        print(f"\nFound {len(selects)} select/dropdown elements in iframe:")

        address_dropdowns = []
        for i, select in enumerate(selects):
            name = select.get_attribute("name")
            id_attr = select.get_attribute("id")
            select_class = select.get_attribute("class")

            # Try to find associated label
            label_text = ""
            if id_attr:
                label = iframe_frame.query_selector(f'label[for="{id_attr}"]')
                if label:
                    label_text = label.text_content()

            options = select.query_selector_all("option")
            print(
                f"Select {i}: name={name}, id={id_attr}, class={select_class}, label='{label_text}'"
            )
            print(f"  Has {len(options)} options")

            if options:
                for j, option in enumerate(options[:5]):  # Show first 5 options
                    value = option.get_attribute("value")
                    text_content = option.text_content()
                    text = text_content.strip() if text_content else ""
                    print(f"    Option {j}: value='{value}', text='{text}'")
                if len(options) > 5:
                    print(f"    ... and {len(options) - 5} more options")

            # Check if this looks like an address dropdown
            search_text = ""
            if label_text:
                search_text += label_text
            if name:
                search_text += name
            if id_attr:
                search_text += id_attr

            if any(
                keyword in search_text.lower()
                for keyword in ["address", "property", "house", "street"]
            ):
                address_dropdowns.append(select)
                print("  *** This looks like an address dropdown! ***")

        # Get all input fields in iframe for complete picture
        inputs = iframe_frame.query_selector_all("input")
        print(f"\nFound {len(inputs)} total input fields in iframe:")

        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_placeholder = inp.get_attribute("placeholder")
            input_value = inp.get_attribute("value")

            # Try to find associated label
            label_text = ""
            if input_id:
                label = iframe_frame.query_selector(f'label[for="{input_id}"]')
                if label:
                    label_text = label.text_content()

            print(f"Input {i}: type={input_type}, name={input_name}, id={input_id}")
            print(
                f"  placeholder='{input_placeholder}', value='{input_value}', label='{label_text}'"
            )

        # Look for buttons in iframe
        buttons = iframe_frame.query_selector_all(
            'button, input[type="submit"], input[type="button"]'
        )
        print(f"\nFound {len(buttons)} buttons in iframe:")

        for i, btn in enumerate(buttons):
            btn_type = btn.get_attribute("type")
            btn_text = btn.text_content()
            btn_value = btn.get_attribute("value")
            btn_onclick = btn.get_attribute("onclick")
            print(
                f"Button {i}: type={btn_type}, text='{btn_text}', value='{btn_value}', onclick={btn_onclick}"
            )

        # Get iframe content text
        iframe_body_text = iframe_frame.evaluate("() => document.body.innerText")
        print("\nIframe content preview (first 1000 chars):")
        print(
            iframe_body_text[:1000] + "..."
            if len(iframe_body_text) > 1000
            else iframe_body_text
        )

        # Take screenshot of iframe (using page screenshot since iframe doesn't have screenshot method)
        screenshot_path = "/tmp/hounslow_iframe_content.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nIframe screenshot saved to: {screenshot_path}")

        # If we found postcode inputs, let's try to understand the workflow
        if postcode_inputs:
            print("\n=== TESTING POSTCODE WORKFLOW ===")
            test_postcode = "TW3 1ES"  # Hounslow postcode

            # Fill the first postcode input
            postcode_input = postcode_inputs[0]
            postcode_input.fill(test_postcode)
            print(f"Filled postcode input with: {test_postcode}")

            # Look for a button to search/submit postcode
            search_buttons = iframe_frame.query_selector_all(
                'button:has-text("Search"), button:has-text("Find"), button:has-text("Continue"), input[type="submit"]'
            )

            if search_buttons:
                print(f"Found {len(search_buttons)} potential search buttons")
                search_button = search_buttons[0]
                print("Clicking search button...")
                search_button.click()

                # Wait for response
                iframe_frame.wait_for_timeout(3000)

                # Check if address dropdown populated
                selects_after = iframe_frame.query_selector_all("select")
                print(f"After postcode search: Found {len(selects_after)} dropdowns")

                for select in selects_after:
                    options = select.query_selector_all("option")
                    if len(options) > 1:  # More than just placeholder
                        print(f"Dropdown now has {len(options)} options:")
                        for j, option in enumerate(options[:10]):  # Show first 10
                            value = option.get_attribute("value")
                            text_content = option.text_content()
                            text = text_content.strip() if text_content else ""
                            print(f"  {j}: value='{value}', text='{text}'")
                        if len(options) > 10:
                            print(f"  ... and {len(options) - 10} more options")
                        break

            # Take another screenshot after postcode entry
            screenshot_path2 = "/tmp/hounslow_after_postcode.png"
            page.screenshot(path=screenshot_path2, full_page=True)
            print(f"Screenshot after postcode entry saved to: {screenshot_path2}")


if __name__ == "__main__":
    debug_iframe()
