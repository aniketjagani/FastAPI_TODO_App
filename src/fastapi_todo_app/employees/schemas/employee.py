"""
Comprehensive Employee Pydantic Models with Advanced Validation
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
import re


class DepartmentEnum(str, Enum):
    """Employee department enumeration"""
    ENGINEERING = "engineering"
    MARKETING = "marketing" 
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"
    SUPPORT = "support"


class EmployeeStatusEnum(str, Enum):
    """Employee status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class EmploymentTypeEnum(str, Enum):
    """Employment type enumeration"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class EmployeeBase(BaseModel):
    """
    Base Employee model with comprehensive validation
    """
    first_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Employee first name"
    )
    last_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Employee last name"
    )
    email: EmailStr = Field(
        ...,
        description="Employee email address"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Employee phone number"
    )
    department: DepartmentEnum = Field(
        ...,
        description="Employee department"
    )
    position: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Employee position/job title"
    )
    salary: Optional[Decimal] = Field(
        None,
        ge=0,
        le=10000000,
        description="Employee annual salary"
    )
    hire_date: date = Field(
        ...,
        description="Employee hire date"
    )
    employment_type: EmploymentTypeEnum = Field(
        default=EmploymentTypeEnum.FULL_TIME,
        description="Type of employment"
    )
    status: EmployeeStatusEnum = Field(
        default=EmployeeStatusEnum.ACTIVE,
        description="Employee status"
    )
    manager_id: Optional[int] = Field(
        None,
        ge=1,
        description="ID of the employee's manager"
    )
    skills: Optional[List[str]] = Field(
        default=[],
        description="Employee skills/competencies"
    )

    @field_validator('first_name', 'last_name', 'position')
    @classmethod
    def validate_names(cls, v):
        """Validate and clean name fields"""
        if v:
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or only whitespace")
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
                raise ValueError("Field contains invalid characters")
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v:
            v = v.strip()
            # Remove common formatting characters
            cleaned = re.sub(r'[\s\-\(\)\.]+', '', v)
            # Check if it's a valid phone format (10-15 digits)
            if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
                raise ValueError("Invalid phone number format")
        return v

    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v):
        """Validate and clean skills list"""
        if v:
            # Remove duplicates and clean whitespace
            cleaned_skills = []
            for skill in v:
                skill = skill.strip().lower()
                if skill and skill not in cleaned_skills:
                    cleaned_skills.append(skill)
            return cleaned_skills
        return []

    @model_validator(mode='after')
    def validate_employee_data(self):
        """Cross-field validation for employee data"""
        hire_date = self.hire_date
        status = self.status
        
        # Check if hire date is not in the future
        if hire_date and hire_date > date.today():
            raise ValueError("Hire date cannot be in the future")
        
        # Check if terminated employee has end date logic
        if status == EmployeeStatusEnum.TERMINATED:
            # Could add end_date field validation here
            pass
            
        return self


class EmployeeCreate(EmployeeBase):
    """Employee creation model"""
    pass


class EmployeeUpdate(BaseModel):
    """
    Employee update model - all fields optional for partial updates
    """
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[DepartmentEnum] = None
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    salary: Optional[Decimal] = Field(None, ge=0, le=10000000)
    employment_type: Optional[EmploymentTypeEnum] = None
    status: Optional[EmployeeStatusEnum] = None
    manager_id: Optional[int] = Field(None, ge=1)
    skills: Optional[List[str]] = None

    @field_validator('first_name', 'last_name', 'position')
    @classmethod
    def validate_names(cls, v):
        """Validate and clean name fields"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or only whitespace")
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
                raise ValueError("Field contains invalid characters")
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is not None:
            v = v.strip()
            cleaned = re.sub(r'[\s\-\(\)\.]+', '', v)
            if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
                raise ValueError("Invalid phone number format")
        return v


class EmployeeResponse(EmployeeBase):
    """
    Employee response model with all fields including computed ones
    """
    id: int = Field(..., description="Employee unique identifier")
    created_at: datetime = Field(..., description="Employee creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    full_name: Optional[str] = Field(None, description="Computed full name")
    years_of_service: Optional[int] = Field(None, description="Years since hire date")

    class Config:
        from_attributes = True


class EmployeeFilter(BaseModel):
    """
    Advanced filtering model for employee search
    """
    department: Optional[DepartmentEnum] = None
    status: Optional[EmployeeStatusEnum] = None
    employment_type: Optional[EmploymentTypeEnum] = None
    manager_id: Optional[int] = Field(None, ge=1)
    min_salary: Optional[Decimal] = Field(None, ge=0)
    max_salary: Optional[Decimal] = Field(None, ge=0)
    hired_after: Optional[date] = None
    hired_before: Optional[date] = None
    skills: Optional[List[str]] = None
    search: Optional[str] = Field(None, max_length=100, description="Search in name, email, position")

    @model_validator(mode='after')
    def validate_salary_range(self):
        """Validate salary range"""
        min_sal = self.min_salary
        max_sal = self.max_salary
        if min_sal is not None and max_sal is not None and min_sal > max_sal:
            raise ValueError("min_salary cannot be greater than max_salary")
        return self

    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate hire date range"""
        after = self.hired_after
        before = self.hired_before
        if after is not None and before is not None and after > before:
            raise ValueError("hired_after cannot be greater than hired_before")
        return self


class EmployeeStats(BaseModel):
    """Employee statistics model"""
    total_employees: int = Field(..., description="Total number of employees")
    active_employees: int = Field(..., description="Number of active employees")
    departments_count: dict = Field(..., description="Employee count by department")
    average_salary: Optional[Decimal] = Field(None, description="Average salary")
    employment_types_count: dict = Field(..., description="Count by employment type")


class EmployeeList(BaseModel):
    """Paginated employee list response"""
    items: List[EmployeeResponse] = Field(..., description="List of employees")
    total: int = Field(..., description="Total number of employees")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class BulkEmployeeCreate(BaseModel):
    """Model for bulk employee creation"""
    employees: List[EmployeeCreate] = Field(
        ..., 
        min_items=1, 
        max_items=100,
        description="List of employees to create"
    )


class BulkStatusUpdate(BaseModel):
    """Model for bulk status updates"""
    employee_ids: List[int] = Field(
        ..., 
        min_items=1,
        description="List of employee IDs to update"
    )
    status: EmployeeStatusEnum = Field(
        ...,
        description="New status for all employees"
    )