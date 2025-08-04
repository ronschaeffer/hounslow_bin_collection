#!/usr/bin/env python3
"""
Enhanced browser automation that handles different postcode lookup scenarios.
"""

from src.hounslow_bin_collection.browser_collector import BrowserWasteCollector


def test_enhanced_workflow():
    """Test enhanced workflow with multiple fallback strategies."""
    with BrowserWasteCollector(headless=True) as collector:
        page = collector.page
        if not page:
            print("Failed to start browser")
            return

        try:
            print("=== ENHANCED HOUNSLOW WORKFLOW TEST ===")
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

            # Take screenshot after clicking tab
            page.screenshot(path="/tmp/hounslow_after_tab.png", full_page=True)
            print("Screenshot saved: /tmp/hounslow_after_tab.png")

            # Find postcode input
            postcode_input = iframe_frame.query_selector("#searchPostcode")
            print(f"Postcode input found: {postcode_input is not None}")

            # Test postcode entry
            test_postcode = "TW7 7HX"
            print(f"Entering postcode: {test_postcode}")

            postcode_input.fill("")
            postcode_input.fill(test_postcode)

            # Try multiple trigger methods
            print("Trying trigger method 1: Tab key...")
            postcode_input.press("Tab")
            iframe_frame.wait_for_timeout(3000)

            # Check if dropdown appeared
            address_dropdown = iframe_frame.query_selector("#selectedAddress")
            is_visible = address_dropdown.is_visible() if address_dropdown else False
            options_count = (
                len(address_dropdown.query_selector_all("option"))
                if address_dropdown
                else 0
            )

            print(
                f"After Tab - Dropdown visible: {is_visible}, Options: {options_count}"
            )

            if not is_visible or options_count <= 1:
                print("Trying trigger method 2: Enter key...")
                postcode_input.focus()
                postcode_input.press("Enter")
                iframe_frame.wait_for_timeout(3000)

                is_visible = (
                    address_dropdown.is_visible() if address_dropdown else False
                )
                options_count = (
                    len(address_dropdown.query_selector_all("option"))
                    if address_dropdown
                    else 0
                )
                print(
                    f"After Enter - Dropdown visible: {is_visible}, Options: {options_count}"
                )

            if not is_visible or options_count <= 1:
                print("Trying trigger method 3: Blur event...")
                postcode_input.evaluate("element => element.blur()")
                iframe_frame.wait_for_timeout(3000)

                is_visible = (
                    address_dropdown.is_visible() if address_dropdown else False
                )
                options_count = (
                    len(address_dropdown.query_selector_all("option"))
                    if address_dropdown
                    else 0
                )
                print(
                    f"After Blur - Dropdown visible: {is_visible}, Options: {options_count}"
                )

            if not is_visible or options_count <= 1:
                print("Trying trigger method 4: JavaScript events...")
                result = iframe_frame.evaluate("""
                    () => {
                        const input = document.getElementById('searchPostcode');
                        if (input) {
                            // Try various events
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            input.dispatchEvent(new Event('keyup', { bubbles: true }));
                            input.dispatchEvent(new Event('blur', { bubbles: true }));

                            // Look for any associated JavaScript functions
                            const formElement = input.closest('form');
                            if (formElement && formElement.onsubmit) {
                                return 'Found form onsubmit';
                            }

                            // Check for onclick handlers on nearby elements
                            const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
                            for (let btn of buttons) {
                                if (btn.onclick || btn.getAttribute('onclick')) {
                                    return `Found button with onclick: ${btn.textContent}`;
                                }
                            }

                            return 'Events dispatched, no handlers found';
                        }
                        return 'Input not found';
                    }
                """)
                print(f"JavaScript events result: {result}")
                iframe_frame.wait_for_timeout(3000)

                is_visible = (
                    address_dropdown.is_visible() if address_dropdown else False
                )
                options_count = (
                    len(address_dropdown.query_selector_all("option"))
                    if address_dropdown
                    else 0
                )
                print(
                    f"After JS events - Dropdown visible: {is_visible}, Options: {options_count}"
                )

            if not is_visible or options_count <= 1:
                print("Trying trigger method 5: Look for search button...")
                # Look for any buttons that might trigger the search
                buttons = iframe_frame.query_selector_all(
                    'button, input[type="button"], input[type="submit"]'
                )
                for i, btn in enumerate(buttons):
                    if btn.is_visible():
                        btn_text = btn.text_content() or ""
                        btn_onclick = btn.get_attribute("onclick")
                        btn_id = btn.get_attribute("id")
                        print(
                            f"Button {i}: '{btn_text}', onclick='{btn_onclick}', id='{btn_id}'"
                        )

                        # Try clicking buttons that might be search-related
                        if any(
                            keyword in btn_text.lower()
                            for keyword in ["search", "find", "lookup", "go"]
                        ):
                            print(f"Clicking search-like button: {btn_text}")
                            btn.click()
                            iframe_frame.wait_for_timeout(3000)

                            is_visible = (
                                address_dropdown.is_visible()
                                if address_dropdown
                                else False
                            )
                            options_count = (
                                len(address_dropdown.query_selector_all("option"))
                                if address_dropdown
                                else 0
                            )
                            print(
                                f"After button click - Dropdown visible: {is_visible}, Options: {options_count}"
                            )
                            break

            # Take final screenshot
            page.screenshot(path="/tmp/hounslow_after_postcode.png", full_page=True)
            print("Final screenshot saved: /tmp/hounslow_after_postcode.png")

            # Show current page state
            if address_dropdown:
                print(
                    f"\nFinal state: Dropdown visible={is_visible}, Options={options_count}"
                )
                if options_count > 1:
                    print("Available options:")
                    options = address_dropdown.query_selector_all("option")
                    for i, option in enumerate(options[:5]):
                        value = option.get_attribute("value")
                        text = option.text_content() or ""
                        print(f"  {i}: value='{value}', text='{text.strip()}'")
                else:
                    print("No addresses found - possible issues:")
                    print("1. Postcode not valid for Hounslow")
                    print("2. Form requires additional fields")
                    print("3. Different trigger mechanism needed")

                    # Check for error messages
                    error_elements = iframe_frame.query_selector_all(
                        '.error, .alert, .warning, [class*="error"], [class*="alert"]'
                    )
                    if error_elements:
                        print("Error messages found:")
                        for elem in error_elements:
                            if elem.is_visible():
                                print(f"  - {elem.text_content()}")

            # Show page content for debugging
            content = iframe_frame.evaluate("() => document.body.innerText")
            print("\nPage content preview (last 500 chars):")
            print(content[-500:] if len(content) > 500 else content)

        except Exception as e:
            print(f"Error in enhanced workflow: {e}")
            page.screenshot(path="/tmp/hounslow_error_enhanced.png", full_page=True)
            print("Error screenshot saved: /tmp/hounslow_error_enhanced.png")


if __name__ == "__main__":
    test_enhanced_workflow()
