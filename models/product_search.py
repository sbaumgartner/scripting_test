from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class ValidationRules(BaseModel):
    min_price: float = Field(ge=0, description="Minimum allowed price")
    max_price: float = Field(gt=0, description="Maximum allowed price")
    min_description_length: int = Field(ge=0, description="Minimum description length")
    max_description_length: int = Field(gt=0, description="Maximum description length")

    @validator('max_price')
    def max_price_must_be_greater_than_min(cls, v, values):
        if 'min_price' in values and v <= values['min_price']:
            raise ValueError('max_price must be greater than min_price')
        return v

    @validator('max_description_length')
    def max_description_must_be_greater_than_min(cls, v, values):
        if 'min_description_length' in values and v <= values['min_description_length']:
            raise ValueError('max_description_length must be greater than min_description_length')
        return v

class ProductSearch(BaseModel):
    name: str = Field(min_length=1, description="Product name to search for")
    expected_price: Decimal = Field(ge=0, description="Expected product price")
    expected_description: str = Field(min_length=1, description="Expected product description")
    validation_rules: ValidationRules

    @validator('expected_price')
    def validate_price_range(cls, v, values):
        if 'validation_rules' in values:
            rules = values['validation_rules']
            if v < rules.min_price or v > rules.max_price:
                raise ValueError(f'Price {v} must be between {rules.min_price} and {rules.max_price}')
        return v

    @validator('expected_description')
    def validate_description_length(cls, v, values):
        if 'validation_rules' in values:
            rules = values['validation_rules']
            if len(v) < rules.min_description_length or len(v) > rules.max_description_length:
                raise ValueError(f'Description length must be between {rules.min_description_length} and {rules.max_description_length} characters')
        return v

class ProductSearchConfig(BaseModel):
    product_search: ProductSearch 