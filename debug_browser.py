#!/usr/bin/env python3
"""
Debug script to explore the Hounslow Council website structure.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def debug_website():
    """Debug the website to understand its structure."""
    with BrowserWasteCollector(headless=True) as collector:
        # Navigate to the page
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        print(f"Navigating to: {collector.FORM_URL}")
        page.goto(collector.FORM_URL)
        page.wait_for_load_state("networkidle")

        # Get page info
        print(f"\nPage title: {page.title()}")
        print(f"Page URL: {page.url}")

        # Get all forms
        forms = page.query_selector_all("form")
        print(f"\nFound {len(forms)} forms on the page")

        for i, form in enumerate(forms):
            action = form.get_attribute("action")
            method = form.get_attribute("method")
            form_id = form.get_attribute("id")
            form_class = form.get_attribute("class")
            print(
                f"Form {i}: action={action}, method={method}, id={form_id}, class={form_class}"
            )

        # Look for postcode-related inputs specifically
        postcode_selectors = [
            'input[name*="postcode" i]',
            'input[id*="postcode" i]',
            'input[placeholder*="postcode" i]',
            'input[placeholder*="post code" i]',
            'input[aria-label*="postcode" i]',
        ]

        print("\nLooking for postcode inputs...")
        for selector in postcode_selectors:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for elem in elements:
                    name = elem.get_attribute("name")
                    id_attr = elem.get_attribute("id")
                    placeholder = elem.get_attribute("placeholder")
                    print(f"  - name={name}, id={id_attr}, placeholder={placeholder}")

        # Look for dropdown/select elements
        selects = page.query_selector_all("select")
        print(f"\nFound {len(selects)} select/dropdown elements:")

        for i, select in enumerate(selects):
            name = select.get_attribute("name")
            id_attr = select.get_attribute("id")
            select_class = select.get_attribute("class")
            # Get first few options
            options = select.query_selector_all("option")
            print(f"Select {i}: name={name}, id={id_attr}, class={select_class}")
            print(f"  Has {len(options)} options")
            if options:
                for j, option in enumerate(options[:3]):  # Show first 3 options
                    value = option.get_attribute("value")
                    text = option.text_content()
                    print(f"    Option {j}: value='{value}', text='{text}'")
                if len(options) > 3:
                    print(f"    ... and {len(options) - 3} more options")

        # Get all input fields
        inputs = page.query_selector_all("input")
        print(f"\nFound {len(inputs)} input fields:")

        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type")
            input_name = inp.get_attribute("name")
            input_id = inp.get_attribute("id")
            input_placeholder = inp.get_attribute("placeholder")
            input_value = inp.get_attribute("value")
            input_class = inp.get_attribute("class")

            print(f"Input {i}:")
            print(f"  type: {input_type}")
            print(f"  name: {input_name}")
            print(f"  id: {input_id}")
            print(f"  placeholder: {input_placeholder}")
            print(f"  value: {input_value}")
            print(f"  class: {input_class}")
            print()

        # Get all buttons
        buttons = page.query_selector_all("button")
        print(f"Found {len(buttons)} buttons:")

        for i, btn in enumerate(buttons):
            btn_type = btn.get_attribute("type")
            btn_class = btn.get_attribute("class")
            btn_text = btn.text_content()
            btn_onclick = btn.get_attribute("onclick")
            print(
                f"Button {i}: type={btn_type}, class={btn_class}, text='{btn_text}', onclick={btn_onclick}"
            )

        # Check for any JavaScript that might load content dynamically
        script_tags = page.query_selector_all("script")
        print(f"\nFound {len(script_tags)} script tags")

        # Look for any text mentioning postcode or address selection
        body_text = page.evaluate("() => document.body.innerText")
        if "postcode" in body_text.lower():
            print("\nFound 'postcode' in page content!")
        if "address" in body_text.lower():
            print("Found 'address' in page content!")
        if "dropdown" in body_text.lower() or "select" in body_text.lower():
            print("Found dropdown/select references in page content!")

        print("\nPage content preview (first 800 chars):")
        print(body_text[:800] + "..." if len(body_text) > 800 else body_text)

        # Save screenshot for debugging
        screenshot_path = "/tmp/hounslow_correct_site.png"
        page.screenshot(path=screenshot_path)
        print(f"\nScreenshot saved to: {screenshot_path}")

        # Check if there are any iframes
        iframes = page.query_selector_all("iframe")
        print(f"\nFound {len(iframes)} iframes")

        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src")
            name = iframe.get_attribute("name")
            iframe_id = iframe.get_attribute("id")
            print(f"Iframe {i}: src={src}, name={name}, id={iframe_id}")

            # If it's a relative URL, make it absolute
            if src and src.startswith("/"):
                print(f"  Full URL: https://my.hounslow.gov.uk{src}")


if __name__ == "__main__":
    debug_website()
