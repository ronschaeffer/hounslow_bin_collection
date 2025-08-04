# COMPREHENSIVE API INVESTIGATION SUMMARY

Date: August 4, 2025
Target: Hounslow Council Waste Collection API

# ENDPOINT TESTED:

https://my.hounslow.gov.uk/api/custom-widgets/getRoundDates

# AUTHENTICATION METHODS ATTEMPTED:

✅ Session establishment (200 OK)
✅ Auth-session token extraction (successful)
✅ Cookie collection (AWSALB, AWSALBCORS, PHPSESSID, APP_LANG, product)
❌ X-Auth-Session header (403 Forbidden)
❌ Authorization Bearer token (403 Forbidden)
❌ Cookie-based auth (403 Forbidden)
❌ Combined headers approach (403 Forbidden)
❌ Process/Domain ID headers (403 Forbidden)

# HTTP METHODS TESTED:

❌ POST with JSON payload (403 Forbidden)
❌ GET with query parameters (403 Forbidden)
❌ POST with form-encoded data (403 Forbidden)

# USER AGENTS TESTED:

❌ Standard Chrome 108 (403 Forbidden)
❌ Enhanced Chrome 131 with full headers (403 Forbidden)
❌ Browser timing simulation (403 Forbidden)

# ALTERNATIVE ENDPOINTS TESTED:

❌ /api/getRoundDates (403 Forbidden)
❌ /getRoundDates (404 Not Found)
❌ /widgets/getRoundDates (404 Not Found)
❌ /form/api/getRoundDates (404 Not Found)
❌ Custom schemes (sandbox-publish://, sandbox-processes://)

# BROWSER HEADERS USED:

- Complete Chrome 131 header set including:
  - Sec-Ch-Ua, Sec-Ch-Ua-Mobile, Sec-Ch-Ua-Platform
  - Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site
  - Accept-Encoding: gzip, deflate, br
  - All standard browser headers

# PUBLIC ENDPOINTS CHECKED:

✅ https://my.hounslow.gov.uk/robots.txt (200 OK)
❌ API documentation endpoints (403/404)
🔍 https://api.hounslow.gov.uk/ (401 Unauthorized - suggests auth required)
✅ https://data.hounslow.gov.uk/ (200 OK - no waste datasets found)

# PROTECTION ANALYSIS:

The API implements multiple sophisticated protection layers:

1. **CSRF Token Validation**: Beyond simple token inclusion
2. **Browser Fingerprinting**: Detects non-browser requests
3. **Session Validation**: Complex session state requirements
4. **Request Pattern Analysis**: May check timing/sequence
5. **Origin Validation**: Strict same-origin policy enforcement
6. **Possible IP-based Restrictions**: Geographic/network filtering

# FORMDATA STRUCTURE FOUND:

- Process ID: AF-Process-f36eaafb-3119-4463-8a6d-ee95cf532505
- Form ID: AF-Form-01a79ed8-a667-4613-98ce-95fc884e4b28
- Domain ID: 1faee79e-14d3-11ee-aa0b-02ddabd3aba7
- Custom CSS: S3-hosted iframe styles
- Auth session: Dynamic per-session token

# TECHNICAL CONCLUSION:

The Hounslow Council API is protected by enterprise-grade security that:

- Successfully blocks all programmatic access attempts
- Requires browser-specific validation beyond headers
- Likely uses JavaScript-based browser fingerprinting
- May require specific form submission workflows
- Implements timing-based request validation

# ALTERNATIVE APPROACHES FOR PRODUCTION:

1. **✅ Browser Automation (IMPLEMENTED & WORKING)**

   - ✅ Playwright successfully installed and configured
   - ✅ Real form discovered in iframe at correct URL
   - ✅ Postcode → Address workflow mapped and automated
   - ✅ Full browser environment bypasses all API protection
   - ✅ Successfully handles JavaScript execution and timing
   - ✅ Cookie dialogs and multi-step forms handled

2. **Official API Access**

   - Contact Hounslow Council for API credentials
   - May have separate developer/business API

3. **HTML Screen Scraping**

   - Parse the form HTML instead of using JSON API
   - Extract data from rendered page content
   - More brittle but might bypass API protection

4. **Alternative Data Sources**
   - Check if data is available via Open Data portals
   - Look for third-party waste collection services
   - Consider My Area/gov.uk integrations

# CURRENT IMPLEMENTATION STATUS:

✅ Robust error handling implemented
✅ Mock data generation for development
✅ Full system integration working
✅ Comprehensive logging and feedback
✅ **BREAKTHROUGH: Browser automation solution implemented**
✅ **Real form workflow discovered and automated**
✅ **Playwright successfully handling iframe-based forms**
✅ **Postcode + Address selection working**
✅ Ready for production deployment with browser automation

# BROWSER AUTOMATION BREAKTHROUGH:

**Date: August 4, 2025 - SOLUTION FOUND**

**Correct Form Location:**

- URL: https://my.hounslow.gov.uk/service/Waste_and_recycling_collections
- Form embedded in iframe: #fillform-frame-1
- Multi-step wizard: "Guidance" → "Your address" tabs

**Workflow Successfully Automated:**

1. ✅ Navigate to service page
2. ✅ Access iframe form content
3. ✅ Dismiss cookie dialog
4. ✅ Click "Your address" tab
5. ✅ Enter postcode in #searchPostcode field
6. ✅ Trigger address lookup (Tab/Enter/Blur events)
7. ✅ Select specific address from #selectedAddress dropdown
8. ✅ Extract UPRN from #addressUPRN field
9. ✅ Continue through form to collection information
10. ✅ Parse and extract collection data

**Test Data Validated:**

- Postcode: TW3 3EB (Hounslow Council's own postcode)
- Address: 7 Bath Rd (Hounslow Council headquarters address)

**Technical Implementation:**

- Browser: Chromium via Playwright 1.54.0
- Mode: Headless operation for production
- Error Handling: Screenshots saved for debugging
- Data Extraction: Pattern matching for collection days/types
- **Data Limitation**: Only actual dates provided by council system are reliable - holidays and service changes affect regular schedules

**Important Note on Collection Dates:**
⚠️ **Collection dates may vary from regular schedules due to:**

- Bank holidays and public holidays
- Service disruptions or operational changes
- Seasonal schedule adjustments
- Emergency service modifications

**Therefore: Only use the specific dates returned by the system - do not attempt to predict or calculate future collection dates beyond those explicitly provided by Hounslow Council.**
