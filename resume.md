# Resume — Hounslow Bin Collection Release

**Session date:** 2026-04-01
**Last commit:** `1d3f967` on main
**Tag:** v0.1.0 (pushed, triggers docker-publish workflow)

---

## Current Status

All code, tests, documentation, and Docker config are complete. The project is ready for public release and deployment.

### What's Done

- Standards alignment with twickenham_events (Makefile, pyproject.toml, CI, pre-commit, ruff rules)
- End-to-end pipeline verified: browser scrape → MQTT → HA entity creation → ICS calendar
- 12 HA entities live (4 waste sensors + next_waste_collection + 5 diagnostics + status + refresh button)
- Consolidated `next_waste_collection` sensor with scheduled/icon/emoji/icon_color for Mushroom card
- Diagnostic sensors: last_run, last_run_status, page_accessible (binary_sensor, >24h alert), collection_count, sw_version
- ICS web server (stdlib, no extra deps) serving calendar files
- Dockerfile with Playwright/Chromium, cron scheduler, ICS web server
- Unraid template updated
- README fully updated for public release (no internal IPs, no secrets)
- config/config.yaml removed from tracking (gitignored)
- CHANGELOG.md finalized for v0.1.0
- Obsidian notes created (Hounslow Bin Collection + Python Projects Overview updated)
- 138 tests passing, lint clean

---

## Remaining Tasks

### 1. Make repo public
**Manual step — cannot be done via CLI/MCP.**

GitHub > `ronschaeffer/hounslow_bin_collection` > Settings > General > Danger Zone > **Change repository visibility > Make public**

### 2. Wait for Docker image build
The v0.1.0 tag push triggers `.github/workflows/docker-publish.yml`. Once the repo is public, verify the image is available:
```bash
docker pull ghcr.io/ronschaeffer/hounslow_bin_collection:0.1.0
```

If the workflow failed while the repo was private, re-trigger it:
- GitHub > Actions > Docker Build & Push > Run workflow > tag: v0.1.0

### 3. Make GHCR package public
After the image is built, the GHCR package may default to private. Make it public:

GitHub > `ronschaeffer/hounslow_bin_collection` > Packages > `hounslow_bin_collection` > Package settings > Danger Zone > **Change visibility > Public**

### 4. Deploy container on Unraid
Use the Unraid template at `unraid-template/HounslowBinCollectionCalendar.xml` or deploy manually:

```
Container image: ghcr.io/ronschaeffer/hounslow_bin_collection:latest
Environment:
  HOUNSLOW_POSTCODE=TW7 7HX
  HOUNSLOW_ADDRESS=132 Worple Rd
  MQTT_ENABLED=true
  MQTT_BROKER_URL=10.10.10.20
  MQTT_BROKER_PORT=1883
  MQTT_SECURITY=none
  CALENDAR_ENABLED=true
  CRON_SCHEDULE=50 2 * * *
  TZ=Europe/London
  HOME_ASSISTANT_ENABLED=true
Ports: 8208:8080
Volumes:
  /mnt/user/appdata/HounslowBinCollection/config:/app/config
  /mnt/user/appdata/HounslowBinCollection/output:/app/output
```

The app config also needs these in config.yaml or env vars:
```
APP_NAME=Hounslow Bin Collection
APP_UNIQUE_ID_PREFIX=hounslow_bins
APP_MANUFACTURER=ronschaeffer
APP_MODEL=Hounslow Bins
APP_SW_VERSION=0.1.0
```

### 5. Add Remote Calendar integration in HA
**Manual step — cannot be done via MCP.**

Settings > Devices & Services > Add Integration > **Remote Calendar**
- URL: `http://10.10.10.20:8208/hounslow_bins.ics`
- Name: "Waste Collection"

This creates `calendar.waste_collection` for the calendar card.

### 6. Verify everything works
- Check HA: all 12 `hounslow_bins_*` entities have correct states
- Check calendar: `calendar.waste_collection` shows Black Bin / Recycling / Food Waste events
- Check dashboard card: Mushroom card shows next collection with correct icon/color
- Check ICS URL: `http://10.10.10.20:8208/hounslow_bins.ics` returns valid ICS content

### 7. Clean up old HA entities (if needed)
If there are stale entities from testing (e.g. `sensor.next_waste_collection` without the `hounslow_bins_` prefix), remove them from HA.

### 8. Optional: Delete stale dependabot branches
The repo has ~15 dependabot branches from when it was using old deps. Consider cleaning them up after going public.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `ha_cards/hounslow_next_collection_card.yaml` | Mushroom card YAML for dashboard |
| `unraid-template/HounslowBinCollectionCalendar.xml` | Unraid container template |
| `config/config.yaml.example` | Config file template |
| `.env.example` | Environment variable template |
| `CHANGELOG.md` | Release notes |
