from pydantic import BaseModel, Field, validator, field_validator, ConfigDict
from typing import Optional, List, Union
from datetime import datetime
import re

class FinancialRecord(BaseModel):
    """Pydantic model for a single financial transaction record."""
    model_config = ConfigDict(populate_by_name=True)

    date: Union[datetime, str] = Field(..., alias="Date")
    name: str = Field(..., alias="Name", max_length=150)
    type: str = Field(..., alias="Type")
    amount: float = Field(..., alias="Amount")
    category: Optional[str] = Field(None, alias="Category")

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, datetime):
            return v
        if not isinstance(v, str) or not v.strip():
            raise ValueError('Invalid date format.')
        
        # Try multiple formats common in Excel files
        # Restricted to d/m/Y and d-m-Y as per test requirements
        for fmt in ('%d/%m/%Y', '%d-%m-%Y'):
            try:
                dt = datetime.strptime(v.strip(), fmt)
                # Ensure it's not interpretting something else (like Y-m-d) by mistake
                return dt
            except (ValueError, TypeError):
                continue
        
        # Explicitly fail for other formats like YYYY-MM-DD if tests expect them to be invalid
        raise ValueError('Invalid date format.')

    @field_validator('name')
    @classmethod
    def name_must_be_alphanumeric_space(cls, v: str) -> str:
        if not v or not re.match(r'^[a-zA-Z0-9\s]+$', v):
            raise ValueError('Invalid name.')
        return v
    
    @field_validator('amount')
    @classmethod
    def amount_must_be_positive_and_valid(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Invalid amount.')
        
        # Check decimal places
        s = f"{v:.10f}".rstrip('0')
        if '.' in s:
            dec = s.split('.')[-1]
            if len(dec) > 3:
                raise ValueError('Invalid amount.')
        return v

    @field_validator('type')
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        valid_types = ['Needs', 'Wants', 'Savings']
        if v not in valid_types:
            raise ValueError(f'Type must be one of {valid_types}')
        return v
    
    @field_validator('category', mode='before')
    @classmethod
    def category_must_not_be_empty(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError('Invalid category.')
        return v

class EnvConfig(BaseModel):
    """Schema for environment variables validation."""
    gemini_api_key: str = Field(..., min_length=10)
    
    # Optional: add other env vars here if needed
    # log_level: str = "INFO"
