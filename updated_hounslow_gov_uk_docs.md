# Updated Documentation for Hounslow Gov UK

Support for schedules provided by [London Borough of Hounslow](https://hounslow.gov.uk/), serving London Borough of Hounslow, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
  - name: hounslow_gov_uk
    args:
      uprn: "UPRN"
      postcode: "POSTCODE"  # Optional but highly recommended
```

### Configuration Variables

**uprn**
*(String | Integer) (required)*

**postcode**
*(String) (optional)*
Optional postcode to improve address matching reliability. When provided, the system can better identify the correct property and handle address variations.

## Example

```yaml
waste_collection_schedule:
  sources:
  - name: hounslow_gov_uk
    args:
      uprn: "100021552942"
      postcode: "TW3 3EB"
```

## How to get the source argument

### Using findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [https://www.findmyaddress.co.uk/](https://www.findmyaddress.co.uk/) and entering in your address details.

### Using browsers developer tools

- Go to [https://my.hounslow.gov.uk/service/Waste_and_recycling_collections](https://my.hounslow.gov.uk/service/Waste_and_recycling_collections)
- Click on "Your address" tab
- Enter your postcode and click search or press Enter
- Right-click on the `Pick an address` dropdown and select `Inspect` or `Inspect Element`
- Expand the `select` element and find the `option` element with your address
- The UPRN is typically included in the `value` attribute

### Using the form directly

1. Go to [https://my.hounslow.gov.uk/service/Waste_and_recycling_collections](https://my.hounslow.gov.uk/service/Waste_and_recycling_collections)
2. Enter your postcode to search for your address
3. Note your exact address format as it appears in the dropdown
4. Use both the UPRN and postcode in your configuration for best results

## Important Notes

- **Enhanced Reliability**: This source now uses browser automation to interact with the council's website, bypassing API security measures that previously caused failures
- **Postcode Recommended**: While the postcode parameter is optional, providing it significantly improves the reliability of address matching
- **Address Variations**: The system automatically handles common address abbreviations (Rd/Road, St/Street, etc.)
- **Error Handling**: If automated access fails, clear error messages will guide you to verify your UPRN manually

## Troubleshooting

If you encounter issues:

1. **Verify your UPRN** by visiting the form manually
2. **Include the postcode** in your configuration
3. **Check the exact address format** as it appears in the council's dropdown
4. **Ensure your UPRN is correct** - incorrect UPRNs will result in no data

The system is designed to be robust and handle the security measures implemented by modern council websites.
