# Fixing the Broken Hounslow Implementation in HACS Waste Collection Schedule

## Problem Analysis

The current Hounslow implementation in the HACS waste collection schedule project is broken because:

1. **API Security Measures**: The Hounslow Council website has implemented security measures that block direct API requests
2. **Wrong URL**: The implementation tries to POST directly to a webpage URL that doesn't accept form submissions
3. **Missing Authentication**: The current approach doesn't handle the iframe-based form system

## Current Broken Implementation

The broken code attempts to make a direct POST request:

```python
API_URL = "https://www.hounslow.gov.uk/homepage/86/recycling_and_waste_collection_day_finder#collectionday"

def fetch(self):
    args = {"UPRN": self._uprn}
    r = requests.post(API_URL, data=args)  # This fails due to security measures
```

## Your Working Solution

Your project successfully uses browser automation (Playwright) to:

1. Navigate to the proper form at `https://my.hounslow.gov.uk/service/Waste_and_recycling_collections`
2. Interact with the iframe containing the form
3. Enter postcodes and select addresses
4. Extract collection data from the results

## Recommended Fix Strategy

To fix the HACS implementation, you can:

### Option 1: Browser Automation Adaptation (Recommended)

Adapt your browser automation approach to work within the HACS framework by:

1. **Adding Playwright dependency** to the HACS project
2. **Replacing the direct API calls** with browser automation
3. **Maintaining the same interface** (`uprn` parameter) for backward compatibility
4. **Adding optional postcode parameter** for better address matching

### Option 2: Enhanced Configuration

Update the documentation to recommend users provide both `uprn` and `postcode`:

```yaml
waste_collection_schedule:
  sources:
  - name: hounslow_gov_uk
    args:
      uprn: "100021552942"
      postcode: "TW3 3EB"  # Optional but recommended
```

## Implementation Approach

Here's the key architectural changes needed:

```python
class Source:
    def __init__(self, uprn: str | int, postcode: str | None = None):
        self._uprn: str = str(uprn)
        self._postcode: str | None = postcode

    def fetch(self) -> list[Collection]:
        # Try browser automation first
        try:
            return self._fetch_with_browser_automation()
        except Exception:
            # Fallback to original method (likely to fail)
            return self._fetch_original_method()

    def _fetch_with_browser_automation(self) -> list[Collection]:
        # Use Playwright to automate the form interaction
        # Based on your working implementation
        pass
```

## Key Benefits of This Approach

1. **Fixes the broken functionality** - No more failed API calls
2. **Backward compatible** - Existing configurations continue to work
3. **Enhanced reliability** - Browser automation bypasses security measures
4. **Future-proof** - Can adapt to website changes more easily
5. **Better error handling** - Clear messages when automation fails

## Implementation Details from Your Project

Your successful implementation shows:

1. **Iframe Navigation**: The form is embedded in an iframe that must be accessed properly
2. **Address Matching**: Enhanced address matching handles abbreviations and variations
3. **Data Extraction**: Robust parsing of collection schedules from the results page
4. **Error Handling**: Graceful fallbacks when automation encounters issues

## Next Steps

To implement this fix:

1. **Extract core browser automation logic** from your project
2. **Adapt it to HACS framework constraints** (headless operation, no GUI dependencies)
3. **Add proper error handling** for server environments
4. **Update documentation** with new optional parameters
5. **Test thoroughly** with various UPRN/postcode combinations

This approach transforms the broken static API implementation into a robust, working solution that can handle the dynamic security measures of modern council websites.

## Files to Update in HACS Project

1. **`custom_components/waste_collection_schedule/waste_collection_schedule/source/hounslow_gov_uk.py`** - Replace the broken implementation
2. **`doc/source/hounslow_gov_uk.md`** - Update documentation with new optional parameters
3. **Add Playwright dependency** to requirements (if not already present)

The key insight from your project is that **browser automation is the reliable solution** for council websites with modern security measures, making direct API approaches obsolete.
