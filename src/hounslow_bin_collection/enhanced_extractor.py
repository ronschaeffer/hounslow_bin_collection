#!/usr/bin/env python3
"""
Enhanced collection data extraction for Hounslow bin collection system.
This module specifically handles the table-based format used by Hounslow Council.
"""

from datetime import datetime
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class HounslowDataExtractor:
    """Enhanced data extractor for Hounslow bin collection results."""

    def __init__(self):
        """Initialize the extractor."""
        self.bin_types = {
            "black wheelie bin": {
                "type": "general_waste",
                "keywords": ["black", "wheelie", "general waste", "refuse"],
                "icon": "🗑️",
            },
            "recycling boxes": {
                "type": "recycling",
                "keywords": [
                    "recycling",
                    "boxes",
                    "plastic",
                    "metal",
                    "card",
                    "paper",
                    "glass",
                ],
                "icon": "♻️",
            },
            "green food waste bin": {
                "type": "food_waste",
                "keywords": ["green", "food waste", "food"],
                "icon": "🥬",
            },
            "brown wheelie bin": {
                "type": "garden_waste",
                "keywords": ["brown", "wheelie", "garden waste", "garden"],
                "icon": "🌱",
            },
        }

    def extract_enhanced_collection_data(
        self, iframe_frame, postcode: str, address: str, uprn: str
    ) -> dict[str, Any]:
        """
        Enhanced extraction method specifically for Hounslow's table format.

        Args:
            iframe_frame: The iframe frame object
            postcode: The postcode that was searched
            address: The selected address
            uprn: The UPRN value

        Returns:
            Dictionary containing detailed collection information
        """
        logger.info("Starting enhanced collection data extraction")

        # Initialize result structure
        result = {
            "postcode": postcode,
            "address": address,
            "uprn": uprn,
            "collections": [],
            "extracted_at": datetime.now().isoformat(),
            "method": "enhanced_table_extraction",
            "bin_schedule": {},
        }

        try:
            # Wait for content to fully load
            iframe_frame.wait_for_timeout(3000)

            # Try multiple methods to get complete content
            page_content = ""
            last_error = None

            # Method 1: Get all text content
            try:
                page_content = (
                    iframe_frame.evaluate("() => document.body.innerText") or ""
                )
                logger.debug("Method 1 - innerText length: %s", len(page_content))
            except Exception as e:
                logger.debug("Method 1 failed: %s", e)
                last_error = e

            # Method 2: If content is too short, try textContent
            if len(page_content) < 500:
                try:
                    page_content = (
                        iframe_frame.evaluate("() => document.body.textContent") or ""
                    )
                    logger.debug("Method 2 - textContent length: %s", len(page_content))
                except Exception as e:
                    logger.debug("Method 2 failed: %s", e)
                    last_error = e

            # Method 3: If still short, wait longer and try again
            if len(page_content) < 500:
                logger.info("Content seems incomplete, waiting longer...")
                iframe_frame.wait_for_timeout(5000)
                try:
                    page_content = (
                        iframe_frame.evaluate("() => document.body.innerText") or ""
                    )
                    logger.debug(
                        "Method 3 - retry innerText length: %s", len(page_content)
                    )
                except Exception as e:
                    logger.debug("Method 3 failed: %s", e)
                    last_error = e

            if not page_content:
                logger.warning("No page content found")
                if last_error:
                    result["extraction_error"] = str(last_error)
                else:
                    result["extraction_error"] = (
                        "Failed to extract page content from iframe"
                    )
                return result

            logger.debug("Final page content length: %s characters", len(page_content))

            # Validate that we're on the right page and it has expected content
            if not self._validate_page_content(page_content):
                logger.error(
                    "Page content validation failed - website format may have changed"
                )
                result["extraction_error"] = (
                    "Website format validation failed - the page structure may have changed"
                )
                return result

            # Log first part of content for debugging
            logger.debug("Content preview: %s...", page_content[:300])

            # Split content into lines for analysis
            lines = [line.strip() for line in page_content.split("\n") if line.strip()]
            logger.debug("Split into %s non-empty lines", len(lines))

            # Extract bin collection data using the table structure
            bin_data = self._extract_bin_collections(lines)

            # Validate that we extracted meaningful data
            if not self._validate_extracted_data(bin_data):
                logger.error(
                    "Extracted data validation failed - website format may have changed"
                )
                result["extraction_error"] = (
                    "No valid collection data found - website format may have changed"
                )
                return result

            # Process each bin type
            for bin_info in bin_data:
                collection_entry = {
                    "text": bin_info["description"],
                    "type": bin_info["bin_type"],
                    "frequency": bin_info["frequency"],
                    "last_collection": bin_info.get("last_collection", ""),
                    "next_collection": bin_info.get("next_collection", ""),
                    "status": bin_info.get("status", ""),
                    "icon": bin_info.get("icon", ""),
                }
                result["collections"].append(collection_entry)

                # Add to bin schedule summary - prioritize entries with actual collection data
                bin_type = bin_info["bin_type"]
                current_entry = result["bin_schedule"].get(bin_type, {})

                # Update if this is the first entry for this bin type, or if current entry is empty but this one has data
                should_update = (
                    bin_type not in result["bin_schedule"]  # First entry for this type
                    or (
                        not current_entry.get("next_date")
                        and bin_info.get("next_collection")
                    )  # Current empty, this has data
                    or (
                        not current_entry.get("frequency") and bin_info.get("frequency")
                    )  # Current has no frequency, this does
                )

                if should_update:
                    result["bin_schedule"][bin_type] = {
                        "next_date": bin_info.get("next_collection", ""),
                        "frequency": bin_info.get("frequency", ""),
                        "last_date": bin_info.get("last_collection", ""),
                        "icon": bin_info.get("icon", ""),
                    }

            # Extract all upcoming dates
            all_dates = self._extract_all_upcoming_dates(lines)
            if all_dates:
                result["collections"].append(
                    {
                        "text": "All upcoming collection dates",
                        "type": "dates",
                        "dates": all_dates,
                    }
                )

            logger.info("Successfully extracted data for %s bin types", len(bin_data))

        except Exception as e:
            logger.error("Error during enhanced extraction: %s", e)
            # Fallback to basic extraction
            result["collections"] = self._basic_fallback_extraction(iframe_frame)
            result["extraction_error"] = str(e)

        return result

    def _extract_bin_collections(self, lines: list[str]) -> list[dict[str, Any]]:
        """
        Extract bin collection data from page lines using Hounslow's table structure.

        Args:
            lines: List of text lines from the page

        Returns:
            List of dictionaries containing bin collection information
        """
        bin_collections = []
        current_bin = None

        i = 0
        while i < len(lines):
            # Check if this line is a bin type header
            bin_type_info = self._identify_bin_type(lines[i])
            if bin_type_info:
                # Save previous bin if we have one
                if current_bin and current_bin.get("description"):
                    bin_collections.append(current_bin)

                # Start new bin
                current_bin = {
                    "description": lines[i],
                    "bin_type": bin_type_info["type"],
                    "icon": bin_type_info["icon"],
                    "frequency": "",
                    "last_collection": "",
                    "next_collection": "",
                    "status": "",
                }

                # Look ahead for collection details
                current_bin.update(self._extract_bin_details(lines, i))

            i += 1

        # Add the last bin if we have one
        if current_bin and current_bin.get("description"):
            bin_collections.append(current_bin)

        return bin_collections

    def _identify_bin_type(self, line: str) -> dict[str, str] | None:
        """
        Identify if a line describes a bin type.

        Args:
            line: Text line to check

        Returns:
            Dictionary with bin type info if identified, None otherwise
        """
        line_lower = line.lower()

        for _bin_name, bin_info in self.bin_types.items():
            # Check if all keywords for this bin type are present
            if any(keyword in line_lower for keyword in bin_info["keywords"]):
                # More specific matching for better accuracy
                if "wheelie" in line_lower and "black" in line_lower:
                    return {"type": "general_waste", "icon": "🗑️"}
                elif "recycling" in line_lower and "box" in line_lower:
                    return {"type": "recycling", "icon": "♻️"}
                elif "food waste" in line_lower and "green" in line_lower:
                    return {"type": "food_waste", "icon": "🥬"}
                elif "garden waste" in line_lower and "brown" in line_lower:
                    return {"type": "garden_waste", "icon": "🌱"}
                elif "recycling" in line_lower:  # Fallback for recycling
                    return {"type": "recycling", "icon": "♻️"}

        return None

    def _extract_bin_details(
        self, lines: list[str], start_index: int
    ) -> dict[str, str]:
        """
        Extract details for a specific bin type from following lines.

        Args:
            lines: All lines from the page
            start_index: Index where bin description starts

        Returns:
            Dictionary with extracted details
        """
        details = {
            "frequency": "",
            "last_collection": "",
            "next_collection": "",
            "status": "",
        }

        # Look at the next 15 lines for relevant information
        end_index = min(len(lines), start_index + 15)

        for i in range(start_index + 1, end_index):
            line = lines[i]
            line_lower = line.lower()

            # Stop if we hit another bin type
            if self._identify_bin_type(line):
                break

            # Extract frequency information
            if "collection day" in line_lower and i + 1 < len(lines):
                freq_line = lines[i + 1]
                if "every" in freq_line.lower() and (
                    "week" in freq_line.lower() or "tuesday" in freq_line.lower()
                ):
                    details["frequency"] = freq_line
                    continue

            # Also check if the current line itself contains frequency info
            if (
                "every" in line_lower
                and ("week" in line_lower or "tuesday" in line_lower)
                and not details["frequency"]
            ):
                details["frequency"] = line

            # Extract last collection date
            if "last collection" in line_lower:
                # Look for date in this line or next line
                date = self._extract_date_from_line(line)
                if not date and i + 1 < len(lines):
                    date = self._extract_date_from_line(lines[i + 1])
                if date:
                    details["last_collection"] = date

            # Extract next collection date
            if "next collection" in line_lower:
                # Look for date in this line or next line
                date = self._extract_date_from_line(line)
                if not date and i + 1 < len(lines):
                    date = self._extract_date_from_line(lines[i + 1])
                if date:
                    details["next_collection"] = date

            # Extract status
            if "completed" in line_lower:
                details["status"] = "completed"
            elif "cannot report" in line_lower:
                details["status"] = "cannot_report"

        return details

    def _calculate_frequency(self, last_date: str, next_date: str) -> str:
        """
        Calculate collection frequency based on last and next collection dates.

        Args:
            last_date: Last collection date in DD/MM/YYYY format
            next_date: Next collection date in DD/MM/YYYY format

        Returns:
            Human readable frequency string
        """
        try:
            last = datetime.strptime(last_date, "%d/%m/%Y")
            next_dt = datetime.strptime(next_date, "%d/%m/%Y")

            # Calculate days between collections
            days_diff = (next_dt - last).days

            # Get day of week for next collection
            day_name = next_dt.strftime("%A")

            if days_diff == 7:
                return f"Every week on {day_name}"
            elif days_diff == 14:
                return f"Every 2 weeks on {day_name}"
            elif days_diff == 28:
                return f"Every 4 weeks on {day_name}"
            elif days_diff >= 30:
                return f"Monthly on {day_name}"
            else:
                return f"Every {days_diff} days"

        except Exception as e:
            logger.debug("Could not calculate frequency: %s", e)
            return ""

    def _extract_date_from_line(self, line: str) -> str | None:
        """
        Extract date from a line using various date patterns.

        Args:
            line: Text line to search

        Returns:
            Extracted date string or None
        """
        # Common date patterns used by Hounslow
        date_patterns = [
            r"\b(\d{2}/\d{2}/\d{4})\b",  # DD/MM/YYYY
            r"\b(\d{1,2}/\d{1,2}/\d{4})\b",  # D/M/YYYY or DD/M/YYYY
            r"\b(\d{4}-\d{2}-\d{2})\b",  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)

        return None

    def _extract_all_upcoming_dates(self, lines: list[str]) -> list[str]:
        """
        Extract all upcoming collection dates from the page.

        Args:
            lines: All lines from the page

        Returns:
            List of upcoming dates
        """
        dates = []

        for line in lines:
            if "next collection" in line.lower():
                date = self._extract_date_from_line(line)
                if date and date not in dates:
                    dates.append(date)

        # Sort dates chronologically
        try:
            dates.sort(key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        except Exception:
            pass  # Keep original order if parsing fails

        return dates

    def _basic_fallback_extraction(self, iframe_frame) -> list[dict[str, Any]]:
        """
        Fallback extraction method if enhanced extraction fails.

        Args:
            iframe_frame: The iframe frame object

        Returns:
            Basic collection data
        """
        logger.warning("Using fallback extraction method")

        try:
            page_content = iframe_frame.evaluate("() => document.body.innerText") or ""

            # Simple pattern matching for basic info
            collections = []

            if "recycling" in page_content.lower():
                collections.append(
                    {"text": "Recycling collection available", "type": "recycling"}
                )

            if (
                "general waste" in page_content.lower()
                or "black" in page_content.lower()
            ):
                collections.append(
                    {
                        "text": "General waste collection available",
                        "type": "general_waste",
                    }
                )

            if "food waste" in page_content.lower():
                collections.append(
                    {"text": "Food waste collection available", "type": "food_waste"}
                )

            if "garden waste" in page_content.lower():
                collections.append(
                    {
                        "text": "Garden waste collection available",
                        "type": "garden_waste",
                    }
                )

            return collections

        except Exception as e:
            logger.error("Fallback extraction failed: %s", e)
            return []

    def _validate_page_content(self, page_content: str) -> bool:
        """
        Validate that the page content has the expected structure for bin collection data.

        Args:
            page_content: The page content to validate

        Returns:
            bool: True if page appears to have expected structure, False otherwise
        """
        try:
            # Check for basic indicators that this is a bin collection page
            required_indicators = [
                "collection",  # Basic collection terminology
                (
                    "bin",
                    "waste",
                    "recycling",
                ),  # Must have at least one waste-related term
                (
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                    "weekly",
                    "every",
                ),  # Schedule indicators
            ]

            page_lower = page_content.lower()

            for indicator in required_indicators:
                if isinstance(indicator, tuple):
                    # Any one of these terms must be present
                    if not any(term in page_lower for term in indicator):
                        logger.warning(
                            "Page validation failed: missing any of %s", indicator
                        )
                        return False
                else:
                    # This specific term must be present
                    if indicator not in page_lower:
                        logger.warning(
                            "Page validation failed: missing '%s'", indicator
                        )
                        return False

            # Check for minimum content length (empty pages or error pages are usually short)
            if len(page_content.strip()) < 100:
                logger.warning(
                    "Page validation failed: content too short (%s chars)",
                    len(page_content),
                )
                return False

            # Check for common error page indicators
            error_indicators = [
                "page not found",
                "404",
                "error occurred",
                "service unavailable",
                "maintenance",
                "temporarily unavailable",
            ]

            for error_indicator in error_indicators:
                if error_indicator in page_lower:
                    logger.warning(
                        "Page validation failed: error indicator '%s' found",
                        error_indicator,
                    )
                    return False

            logger.debug("Page content validation passed")
            return True

        except Exception as e:
            logger.error("Page validation error: %s", e)
            return False

    def _validate_extracted_data(self, bin_data: list[dict]) -> bool:
        """
        Validate that the extracted data contains meaningful bin collection information.

        Args:
            bin_data: List of extracted bin collection data

        Returns:
            bool: True if data appears valid, False otherwise
        """
        try:
            if not bin_data:
                logger.warning("No bin data extracted")
                return False

            # Check for minimum number of expected bins (at least general waste or recycling)
            if len(bin_data) < 1:
                logger.warning("Too few bin collections found")
                return False

            # Validate each bin entry has required fields
            required_fields = ["bin_type", "description"]
            for i, bin_info in enumerate(bin_data):
                for field in required_fields:
                    if field not in bin_info or not bin_info[field]:
                        logger.warning("Bin %s missing required field '%s'", i, field)
                        return False

                # Check that bin_type is one we recognize
                if bin_info["bin_type"] not in [
                    "general_waste",
                    "recycling",
                    "food_waste",
                    "garden_waste",
                ]:
                    logger.warning("Unrecognized bin type: %s", bin_info["bin_type"])
                    # Don't fail here as new bin types might be added

            # Check that at least one bin has meaningful frequency or date information
            has_schedule_info = False
            for bin_info in bin_data:
                if (
                    (bin_info.get("frequency") and bin_info["frequency"] != "Unknown")
                    or bin_info.get("next_collection")
                    or bin_info.get("last_collection")
                ):
                    has_schedule_info = True
                    break

            if not has_schedule_info:
                logger.warning("No bins have schedule information")
                return False

            logger.debug("Extracted data validation passed for %s bins", len(bin_data))
            return True

        except Exception as e:
            logger.error("Data validation error: %s", e)
            return False
