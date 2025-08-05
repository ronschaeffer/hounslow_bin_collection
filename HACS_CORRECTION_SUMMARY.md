# Corrected Hounslow HACS Implementation

## Summary

Created `hounslow_gov_uk_hacs_fixed.py` - a corrected implementation for the HACS waste collection schedule that fixes the broken Hounslow source.

## Key Changes from Original HACS Implementation

### 1. **Parameter Change: UPRN → Postcode + Address Hint**
- **Before**: Used `uprn` parameter (Unique Property Reference Number)
- **After**: Uses `postcode` + optional `address_hint` (street address)
- **Reason**: Your working implementation shows street addresses are now the primary search method

### 2. **Added Playwright Browser Automation**
- **Unique Feature**: This would be the **first HACS source** to use Playwright
- **All other HACS sources** use simple HTTP requests with `requests` + `BeautifulSoup`
- **Required Because**: Hounslow's iframe-based form with security measures blocks direct API calls

### 3. **Enhanced Address Matching**
- Uses intelligent address matching based on your working implementation
- Scores addresses by matching words from the `address_hint`
- Falls back to first available address if no good match found

## Implementation Structure

```python
class Source:
    def __init__(self, postcode: str, address_hint: str | None = None):
        # Uses postcode + address_hint instead of UPRN

    def fetch(self) -> list[Collection]:
        # Primary: Browser automation (most reliable)
        # Fallback: Original HTTP method (likely to fail)
```

## Test Cases

```python
TEST_CASES = {
    "Hounslow High Street": {"postcode": "TW3 1ES", "address_hint": "High Street"},
    "Bath Road": {"postcode": "TW5 9QE", "address_hint": "Bath Road"},
    "Postcode only": {"postcode": "TW4 6JP"},
}
```

## HACS Integration Notes

### Dependencies Required
- `playwright` (new dependency for HACS)
- `requests` (already used by HACS)
- `beautifulsoup4` (already used by HACS)

### Playwright Browsers
HACS would need to install Playwright browsers:
```bash
playwright install chromium
```

## Key Differences from Other HACS Sources

1. **Browser Automation**: Only Hounslow source uses full browser automation
2. **Complex Form Handling**: Handles iframe-based forms with JavaScript
3. **Address Matching**: Intelligent matching vs exact parameter lookup
4. **Security Bypass**: Works around anti-automation measures

## Why This Approach is Necessary

1. **API Blocking**: Direct HTTP requests are blocked by security measures
2. **Complex Form**: Iframe-based form requires browser interaction
3. **Dynamic Content**: Address lookup requires JavaScript execution
4. **Street Address Focus**: Modern approach uses addresses, not UPRNs

## Migration Path for HACS

The HACS project would need to:

1. **Add Playwright dependency** to their requirements
2. **Install browser engines** in their deployment
3. **Update documentation** about the new parameter structure
4. **Consider browser automation infrastructure** for server environments

This represents a significant shift for HACS since it's the first source requiring full browser automation, but it's necessary to handle modern security-protected council websites.
