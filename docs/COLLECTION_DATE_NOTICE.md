# Collection Date Reliability Notice

## ⚠️ Important Limitation: Collection Dates May Vary

When using the Hounslow bin collection browser automation, please be aware that **collection dates can vary from the regular schedule** due to several factors:

### Factors That Affect Collection Dates:

1. **Bank Holidays & Public Holidays**

   - Collections may be delayed by 1-2 days
   - Christmas/New Year periods often have modified schedules

2. **Service Disruptions**

   - Weather conditions (snow, flooding)
   - Vehicle breakdowns or staffing issues
   - Road closures or traffic disruptions

3. **Operational Changes**

   - Route optimizations
   - Seasonal schedule adjustments
   - Service improvements or modifications

4. **Emergency Situations**
   - Local emergencies requiring resource reallocation
   - Health and safety incidents

### Best Practices:

✅ **DO:**

- Use only the specific dates provided by the council system
- Check the council website regularly for any service updates
- Set up notifications from Hounslow Council for collection changes
- Keep an eye on local council communications

❌ **DON'T:**

- Predict or calculate future collection dates beyond those shown
- Assume regular weekly/fortnightly patterns will always hold
- Rely solely on automated data without checking for updates

### Data Accuracy:

The browser automation extracts **real-time data directly from Hounslow Council's official system**, ensuring you get the most current information available. However, this data reflects the schedule at the time of extraction and may be subject to subsequent changes.

### Recommended Usage:

1. **Check regularly** - Run the automation weekly to get updated schedules
2. **Cross-reference** - Verify important dates with the council website
3. **Stay informed** - Follow @HounslowCouncil on social media for urgent updates
4. **Plan ahead** - Don't wait until the last minute to put bins out

### Example Usage:

```bash
# Using Hounslow Council's address for testing
poetry run python demo_final.py

# Using your own address
poetry run python -c "
from src.hounslow_bin_collection.browser_collector import fetch_collection_data_browser
result = fetch_collection_data_browser('YOUR_POSTCODE', 'YOUR_ADDRESS')
print(result['collections'])
"
```

**Default Test Address:** The tool uses Hounslow Council's own address (7 Bath Rd, Hounslow TW3 3EB) for testing and examples.

---

_This automation tool provides a convenient way to access collection data, but the responsibility for staying informed about any changes remains with the user._
