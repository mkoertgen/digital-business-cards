"""Data models for contacts and configuration."""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class Contact(BaseModel):
    """Contact information from Azure AD."""
    
    id: str = Field(..., description="Short ID (e.g., MKo)")
    name: str = Field(..., description="Full display name")
    email: EmailStr = Field(..., description="Email address")
    title: Optional[str] = Field(default=None, description="Job title")
    department: Optional[str] = Field(default=None, description="Department")
    phone: Optional[str] = Field(default=None, description="Phone number")
    mobile: Optional[str] = Field(default=None, description="Mobile number")
    manager: Optional[str] = Field(default=None, description="Manager ID")
    company: str = Field(default="", description="Company name")
    active: bool = Field(default=True, description="Is active")
    
    @property
    def full_name_parts(self) -> tuple[str, str]:
        """Split name into first and last name."""
        parts = self.name.strip().split(maxsplit=1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], ""


class QRConfig(BaseModel):
    """QR code generation configuration."""
    
    size: int = Field(default=256, description="QR code size in pixels")
    border: int = Field(default=4, description="Border size in modules")
    format: str = Field(default="png", description="Output format (png/svg)")
    error_correction: str = Field(default="M", description="Error correction level (L/M/Q/H)")
