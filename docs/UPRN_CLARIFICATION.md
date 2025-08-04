# 🔍 UPRN vs Browser Methods - Clarification & Status

## ✅ **CLARIFIED: UPRN Environment Variable Usage**

You were absolutely correct! The `UPRN` environment variable is **not used by the browser collector**. Here's the complete picture:

## 🎯 **Two Separate Systems**

### **1. Browser Automation (WORKING ✅)**
- **File**: `browser_collector.py`
- **Method**: Browser automation with Playwright
- **Environment Variables**: `HOUNSLOW_POSTCODE` + `HOUNSLOW_ADDRESS`
- **Status**: **FULLY WORKING** with enhanced address matching
- **Use Case**: Real-time data collection from council website

### **2. Direct API (BLOCKED ❌)**
- **File**: `waste_sync.py`
- **Method**: Direct HTTP API calls
- **Environment Variable**: `UPRN`
- **Status**: **BLOCKED** by council security (returns mock data)
- **Use Case**: Legacy approach, now superseded by browser automation

## 🚨 **Key Findings**

### **UPRN Environment Variable Reality**
```bash
# This is ONLY used by waste_sync.py (which is blocked)
export UPRN=100021577775

# This is used by browser_collector.py (which works)
export HOUNSLOW_POSTCODE=TW3 3EB
export HOUNSLOW_ADDRESS=7 Bath Rd
```

### **What Actually Works**
1. **Browser collector** uses postcode + address hint
2. **Browser collector** discovers the UPRN automatically from the council website
3. **Enhanced matching** handles address abbreviations automatically
4. **Manual verification** provides 100% accuracy fallback

## 📋 **Updated Recommendations**

### **For Production (Docker/Home Assistant)**
```yaml
environment:
  # WORKING METHOD
  - HOUNSLOW_POSTCODE=your_postcode
  - HOUNSLOW_ADDRESS=your_address

  # LEGACY METHOD (blocked)
  # - UPRN=your_uprn  # Don't use this
```

### **For Development**
```bash
# Use browser automation
export HOUNSLOW_POSTCODE="TW3 3EB"
export HOUNSLOW_ADDRESS="7 Bath Rd"

# Don't use UPRN for browser automation
# export UPRN=100021577775  # This won't help
```

## 🎯 **Browser Collector UPRN Discovery**

The browser collector **automatically discovers** the UPRN:

1. **Enters postcode** → Gets address dropdown
2. **Matches address** → Selects from dropdown
3. **Extracts UPRN** → Council website populates UPRN field
4. **Returns data** → Includes discovered UPRN in results

```python
# Example output from browser collector
{
    'address': 'Coffee Republic, Hounslow House, 7, Bath Road, Hounslow, TW3 3EB',
    'uprn': '10094942523',  # ← Automatically discovered!
    'postcode': 'TW3 3EB',
    'collections': [...]
}
```

## 💡 **Why The Confusion**

1. **Config system** loads UPRN from environment variables
2. **waste_sync.py** uses UPRN for direct API calls (blocked)
3. **browser_collector.py** doesn't use the UPRN environment variable at all
4. **Documentation** initially suggested both methods were equivalent

## ✅ **Corrected Documentation**

### **Environment Variables (Updated)**
| Variable             | Used By           | Status   | Purpose |
|---------------------|------------------|----------|---------|
| `HOUNSLOW_POSTCODE` | browser_collector.py | ✅ WORKING | Address lookup |
| `HOUNSLOW_ADDRESS`  | browser_collector.py | ✅ WORKING | Enhanced matching |
| `UPRN`              | waste_sync.py    | ❌ BLOCKED | Direct API (legacy) |

### **Recommendations (Updated)**
- ✅ **Use**: Browser automation with postcode + address
- ❌ **Don't use**: UPRN environment variable for browser automation
- 🎯 **Best practice**: Let browser collector discover UPRN automatically

## 🔗 **Manual Verification Still Works**
For 100% accuracy: https://my.hounslow.gov.uk/service/Waste_and_recycling_collections

---

**🎯 SUMMARY: The UPRN environment variable is legacy and not used by the working browser automation system. Use `HOUNSLOW_POSTCODE` + `HOUNSLOW_ADDRESS` for reliable results.**
