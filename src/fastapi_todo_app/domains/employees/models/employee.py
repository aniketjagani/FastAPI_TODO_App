"""
Employee SQLAlchemy Model for PostgreSQL
"""

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.database import Base
from ..schemas.employee import DepartmentEnum, EmployeeStatusEnum, EmploymentTypeEnum


class Employee(Base):
    """
    Employee SQLAlchemy model for PostgreSQL database
    """
    __tablename__ = "employees"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal information
    first_name = Column(String(50), nullable=False, index=True)
    last_name = Column(String(50), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    
    # Employment information
    department = Column(SQLEnum(DepartmentEnum), nullable=False, index=True)
    position = Column(String(100), nullable=False)
    salary = Column(Numeric(10, 2), nullable=True)  # Precision for currency
    hire_date = Column(Date, nullable=False, index=True)
    employment_type = Column(SQLEnum(EmploymentTypeEnum), nullable=False, default=EmploymentTypeEnum.FULL_TIME)
    status = Column(SQLEnum(EmployeeStatusEnum), nullable=False, default=EmployeeStatusEnum.ACTIVE, index=True)
    
    # Relationships
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    manager = relationship("Employee", remote_side=[id], back_populates="direct_reports")
    direct_reports = relationship("Employee", back_populates="manager")
    
    # Skills (PostgreSQL ARRAY)
    skills = Column(ARRAY(String(50)), nullable=True, default=[])
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Employee(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"

    @property
    def full_name(self) -> str:
        """Get employee's full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def years_of_service(self) -> int:
        """Calculate years of service"""
        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )

    def to_dict(self) -> dict:
        """
        Convert Employee model to dictionary for Pydantic serialization
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "position": self.position,
            "salary": self.salary,
            "hire_date": self.hire_date,
            "employment_type": self.employment_type,
            "status": self.status,
            "manager_id": self.manager_id,
            "skills": self.skills or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "full_name": self.full_name,
            "years_of_service": self.years_of_service,
        }

    @classmethod
    def from_pydantic(cls, employee_data):
        """
        Create Employee instance from Pydantic model data
        """
        return cls(
            first_name=employee_data.first_name,
            last_name=employee_data.last_name,
            email=employee_data.email,
            phone=employee_data.phone,
            department=employee_data.department,
            position=employee_data.position,
            salary=employee_data.salary,
            hire_date=employee_data.hire_date,
            employment_type=employee_data.employment_type,
            status=employee_data.status,
            manager_id=employee_data.manager_id,
            skills=employee_data.skills or [],
        )

    def update_from_pydantic(self, employee_data):
        """
        Update Employee instance from Pydantic model data
        """
        for field, value in employee_data.dict(exclude_unset=True).items():
            if hasattr(self, field):
                setattr(self, field, value)
        
        # Update timestamp
        self.updated_at = func.now()
        return self