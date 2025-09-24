"""
Employee Service Layer with PostgreSQL Integration
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..models.employee import Employee
from ..schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeFilter, EmployeeStats,
    DepartmentEnum, EmployeeStatusEnum, EmploymentTypeEnum
)


class EmployeeService:
    """
    Employee business logic service
    """

    @staticmethod
    def create_employee(db: Session, employee_data: EmployeeCreate) -> Employee:
        """
        Create a new employee with Pydantic validation
        """
        # Check if email already exists
        existing_employee = db.query(Employee).filter(Employee.email == employee_data.email).first()
        if existing_employee:
            raise ValueError(f"Employee with email {employee_data.email} already exists")
        
        # Validate manager exists if provided
        if employee_data.manager_id:
            manager = db.query(Employee).filter(Employee.id == employee_data.manager_id).first()
            if not manager:
                raise ValueError(f"Manager with ID {employee_data.manager_id} not found")
        
        # Create employee from Pydantic data
        db_employee = Employee.from_pydantic(employee_data)
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee

    @staticmethod
    def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
        """
        Get employee by ID
        """
        return db.query(Employee).filter(Employee.id == employee_id).first()

    @staticmethod
    def get_employees(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filter_params: Optional[EmployeeFilter] = None
    ) -> tuple[List[Employee], int]:
        """
        Get employees with advanced filtering and pagination
        """
        query = db.query(Employee)
        
        # Apply filters if provided
        if filter_params:
            if filter_params.department:
                query = query.filter(Employee.department == filter_params.department)
            
            if filter_params.status:
                query = query.filter(Employee.status == filter_params.status)
            
            if filter_params.employment_type:
                query = query.filter(Employee.employment_type == filter_params.employment_type)
            
            if filter_params.manager_id:
                query = query.filter(Employee.manager_id == filter_params.manager_id)
            
            if filter_params.min_salary is not None:
                query = query.filter(Employee.salary >= filter_params.min_salary)
            
            if filter_params.max_salary is not None:
                query = query.filter(Employee.salary <= filter_params.max_salary)
            
            if filter_params.hired_after:
                query = query.filter(Employee.hire_date >= filter_params.hired_after)
            
            if filter_params.hired_before:
                query = query.filter(Employee.hire_date <= filter_params.hired_before)
            
            if filter_params.skills:
                for skill in filter_params.skills:
                    query = query.filter(Employee.skills.any(skill.lower()))
            
            if filter_params.search:
                search_term = f"%{filter_params.search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Employee.first_name).like(search_term),
                        func.lower(Employee.last_name).like(search_term),
                        func.lower(Employee.email).like(search_term),
                        func.lower(Employee.position).like(search_term)
                    )
                )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        employees = query.order_by(desc(Employee.created_at)).offset(skip).limit(limit).all()
        
        return employees, total

    @staticmethod
    def update_employee(db: Session, employee_id: int, employee_data: EmployeeUpdate) -> Optional[Employee]:
        """
        Update employee with Pydantic validation
        """
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not db_employee:
            return None
        
        # Validate email uniqueness if updating email
        if employee_data.email and employee_data.email != db_employee.email:
            existing = db.query(Employee).filter(
                and_(Employee.email == employee_data.email, Employee.id != employee_id)
            ).first()
            if existing:
                raise ValueError(f"Employee with email {employee_data.email} already exists")
        
        # Validate manager exists if provided
        if employee_data.manager_id and employee_data.manager_id != db_employee.manager_id:
            if employee_data.manager_id == employee_id:
                raise ValueError("Employee cannot be their own manager")
            
            manager = db.query(Employee).filter(Employee.id == employee_data.manager_id).first()
            if not manager:
                raise ValueError(f"Manager with ID {employee_data.manager_id} not found")
        
        # Update employee from Pydantic data
        db_employee.update_from_pydantic(employee_data)
        db.commit()
        db.refresh(db_employee)
        return db_employee

    @staticmethod
    def delete_employee(db: Session, employee_id: int) -> bool:
        """
        Delete employee (soft delete by setting status to TERMINATED)
        """
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not db_employee:
            return False
        
        # Check if employee has direct reports
        direct_reports_count = db.query(Employee).filter(Employee.manager_id == employee_id).count()
        if direct_reports_count > 0:
            raise ValueError(f"Cannot delete employee with {direct_reports_count} direct reports. Please reassign them first.")
        
        # Soft delete by setting status
        db_employee.status = EmployeeStatusEnum.TERMINATED
        db.commit()
        return True

    @staticmethod
    def get_employee_stats(db: Session) -> EmployeeStats:
        """
        Get comprehensive employee statistics
        """
        # Basic counts
        total_employees = db.query(Employee).count()
        active_employees = db.query(Employee).filter(Employee.status == EmployeeStatusEnum.ACTIVE).count()
        
        # Department breakdown
        dept_stats = db.query(
            Employee.department, func.count(Employee.id)
        ).group_by(Employee.department).all()
        departments_count = {dept.value: count for dept, count in dept_stats}
        
        # Employment type breakdown
        type_stats = db.query(
            Employee.employment_type, func.count(Employee.id)
        ).group_by(Employee.employment_type).all()
        employment_types_count = {emp_type.value: count for emp_type, count in type_stats}
        
        # Average salary
        avg_salary = db.query(func.avg(Employee.salary)).filter(
            Employee.salary.isnot(None)
        ).scalar()
        
        return EmployeeStats(
            total_employees=total_employees,
            active_employees=active_employees,
            departments_count=departments_count,
            average_salary=Decimal(str(avg_salary)) if avg_salary else None,
            employment_types_count=employment_types_count
        )

    @staticmethod
    def get_employees_by_department(db: Session, department: DepartmentEnum) -> List[Employee]:
        """
        Get all employees in a specific department
        """
        return db.query(Employee).filter(Employee.department == department).all()

    @staticmethod
    def get_employees_by_manager(db: Session, manager_id: int) -> List[Employee]:
        """
        Get all direct reports for a manager
        """
        return db.query(Employee).filter(Employee.manager_id == manager_id).all()

    @staticmethod
    def search_employees(db: Session, search_term: str, limit: int = 50) -> List[Employee]:
        """
        Search employees by name, email, or position
        """
        search_pattern = f"%{search_term.lower()}%"
        return db.query(Employee).filter(
            or_(
                func.lower(Employee.first_name).like(search_pattern),
                func.lower(Employee.last_name).like(search_pattern),
                func.lower(Employee.email).like(search_pattern),
                func.lower(Employee.position).like(search_pattern)
            )
        ).limit(limit).all()

    @staticmethod
    def bulk_create_employees(db: Session, employees_data: List[EmployeeCreate]) -> List[Employee]:
        """
        Create multiple employees in bulk
        """
        created_employees = []
        emails = [emp.email for emp in employees_data]
        
        # Check for duplicate emails within the batch
        if len(emails) != len(set(emails)):
            raise ValueError("Duplicate emails found in the batch")
        
        # Check for existing emails in database
        existing_emails = db.query(Employee.email).filter(Employee.email.in_(emails)).all()
        if existing_emails:
            existing_list = [email[0] for email in existing_emails]
            raise ValueError(f"The following emails already exist: {existing_list}")
        
        try:
            for employee_data in employees_data:
                db_employee = Employee.from_pydantic(employee_data)
                db.add(db_employee)
                created_employees.append(db_employee)
            
            db.commit()
            
            # Refresh all created employees
            for emp in created_employees:
                db.refresh(emp)
                
            return created_employees
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def bulk_update_status(db: Session, employee_ids: List[int], new_status: EmployeeStatusEnum) -> int:
        """
        Update status for multiple employees
        """
        updated_count = db.query(Employee).filter(
            Employee.id.in_(employee_ids)
        ).update(
            {Employee.status: new_status}, 
            synchronize_session=False
        )
        db.commit()
        return updated_count