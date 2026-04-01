# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Aligned project standards with twickenham_events reference implementation
- Updated Python target to 3.11+
- Added Makefile with standard targets (check, fix, test, ci-check)
- Expanded ruff lint rules for Home Assistant compatibility
- Added pre-push pytest hook and additional pre-commit checks
- Consolidated CI workflows (ci, code-quality, docker-publish, local-consistency, version-bump)
- Moved dev dependencies to Poetry group
- Added ha-mqtt-publisher as explicit dependency
- Added CLI entry point (`hounslow-bins`)

### Removed
- Root-level legacy scripts (bin_lookup.py, bin_schedule.py, etc.)
- Session summary documents (COMPLETION_SUMMARY.md, etc.)
- Redundant CI workflows (deploy.yml, publish-docker.yml, security.yml, release.yml)
