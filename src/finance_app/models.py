from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime
import re

class FinancialRecord(BaseModel):
    """Pydantic model for a single financial transaction record."""
    date: datetime = Field(..., alias="Date")
    name: str = Field(..., alias="Name", max_length=150)
    type: str = Field(..., alias="Type")
    amount: float = Field(..., alias="Amount", gt=0)
    category: Optional[str] = Field(None, alias="Category")

    @field_validator('name')
    @classmethod
    def name_must_be_alphanumeric_space(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9\s]+$', v):
            raise ValueError('Name must contain only alphanumeric characters and spaces')
        return v

    @field_validator('type')
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        valid_types = ['Needs', 'Wants', 'Savings']
        if v not in valid_types:
            raise ValueError(f'Type must be one of {valid_types}')
        return v

    @field_validator('amount')
    @classmethod
    def amount_must_have_proper_decimals(cls, v: float) -> float:
        s = str(v)
        if '.' in s:
            dec = s.split('.')[-1]
            if len(dec) > 3:
                raise ValueError('Amount cannot have more than 3 decimal places')
        return v

class EnvConfig(BaseModel):
    """Schema for environment variables validation."""
    gemini_api_key: str = Field(..., min_length=10)
    
    # Optional: add other env vars here if needed
    # log_level: str = "INFO"
