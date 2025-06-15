"""
Date resolution tool for the RegHealth Navigator system.
This tool is responsible for resolving relative time references to absolute dates.
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import dateparser
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field

class DateRange(BaseModel):
    """Represents a date range with start and end dates."""
    start_date: datetime = Field(..., description="The start date of the range")
    end_date: datetime = Field(..., description="The end date of the range")

class DateResolver:
    """Tool for resolving relative time references to absolute dates."""
    
    def __init__(self):
        """Initialize the date resolver with common time reference mappings."""
        self.now = datetime.now()
        
        # Common time reference mappings
        self.time_references = {
            "this year": lambda: DateRange(
                start_date=datetime(self.now.year, 1, 1),
                end_date=datetime(self.now.year, 12, 31)
            ),
            "last year": lambda: DateRange(
                start_date=datetime(self.now.year - 1, 1, 1),
                end_date=datetime(self.now.year - 1, 12, 31)
            ),
            "this quarter": lambda: self._get_quarter_range(self.now),
            "last quarter": lambda: self._get_quarter_range(self.now - relativedelta(months=3)),
            "this month": lambda: DateRange(
                start_date=datetime(self.now.year, self.now.month, 1),
                end_date=(datetime(self.now.year, self.now.month + 1, 1) - timedelta(days=1))
            ),
            "last month": lambda: DateRange(
                start_date=datetime(self.now.year, self.now.month - 1, 1),
                end_date=(datetime(self.now.year, self.now.month, 1) - timedelta(days=1))
            )
        }
    
    def _get_quarter_range(self, date: datetime) -> DateRange:
        """Get the date range for a quarter.
        
        Args:
            date: The date to get the quarter range for
            
        Returns:
            DateRange: The date range for the quarter
        """
        quarter = (date.month - 1) // 3
        start_month = quarter * 3 + 1
        end_month = start_month + 2
        
        start_date = datetime(date.year, start_month, 1)
        if end_month == 12:
            end_date = datetime(date.year, 12, 31)
        else:
            end_date = datetime(date.year, end_month + 1, 1) - timedelta(days=1)
            
        return DateRange(start_date=start_date, end_date=end_date)
    
    def resolve_date(self, time_ref: str) -> Optional[DateRange]:
        """Resolve a time reference to a date range.
        
        Args:
            time_ref: The time reference to resolve
            
        Returns:
            Optional[DateRange]: The resolved date range or None if not resolvable
        """
        # Check if it's a known time reference
        time_ref = time_ref.lower()
        if time_ref in self.time_references:
            return self.time_references[time_ref]()
        
        # Try to parse as a relative date
        try:
            parsed_date = dateparser.parse(time_ref)
            if parsed_date:
                # If it's a single date, create a range for that day
                return DateRange(
                    start_date=datetime(parsed_date.year, parsed_date.month, parsed_date.day),
                    end_date=datetime(parsed_date.year, parsed_date.month, parsed_date.day, 23, 59, 59)
                )
        except:
            pass
        
        return None
    
    def resolve_date_range(self, start_ref: str, end_ref: str) -> Optional[DateRange]:
        """Resolve a date range from start and end references.
        
        Args:
            start_ref: The start time reference
            end_ref: The end time reference
            
        Returns:
            Optional[DateRange]: The resolved date range or None if not resolvable
        """
        start_date = self.resolve_date(start_ref)
        end_date = self.resolve_date(end_ref)
        
        if start_date and end_date:
            return DateRange(
                start_date=start_date.start_date,
                end_date=end_date.end_date
            )
        
        return None 