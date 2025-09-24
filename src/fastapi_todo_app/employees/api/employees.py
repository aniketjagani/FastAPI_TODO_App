"""
Employee API Endpoints with PostgreSQL Integration
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.employee import Employee
from ..schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeFilter,
    EmployeeList, EmployeeStats, BulkEmployeeCreate, BulkStatusUpdate,
    DepartmentEnum, EmployeeStatusEnum
)
from ..services.employee_service import EmployeeService

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new employee with comprehensive Pydantic validation
    """
    try:
        db_employee = EmployeeService.create_employee(db, employee)
        return EmployeeResponse(**db_employee.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create employee: {str(e)}")


@router.get("/", response_model=EmployeeList)
def get_employees(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    department: Optional[DepartmentEnum] = Query(None, description="Filter by department"),
    status: Optional[EmployeeStatusEnum] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, max_length=100, description="Search in name, email, position"),
    db: Session = Depends(get_db)
):
    """
    Get employees with pagination and filtering
    """
    try:
        # Create filter object
        filter_params = EmployeeFilter(
            department=department,
            status=status,
            search=search
        ) if any([department, status, search]) else None
        
        employees, total = EmployeeService.get_employees(db, skip, limit, filter_params)
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        return EmployeeList(
            items=[EmployeeResponse(**emp.to_dict()) for emp in employees],
            total=total,
            page=current_page,
            per_page=limit,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve employees: {str(e)}")


@router.get("/stats", response_model=EmployeeStats)
def get_employee_statistics(db: Session = Depends(get_db)):
    """
    Get comprehensive employee statistics
    """
    try:
        return EmployeeService.get_employee_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/department/{department}", response_model=List[EmployeeResponse])
def get_employees_by_department(
    department: DepartmentEnum,
    db: Session = Depends(get_db)
):
    """
    Get all employees in a specific department
    """
    try:
        employees = EmployeeService.get_employees_by_department(db, department)
        return [EmployeeResponse(**emp.to_dict()) for emp in employees]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employees by department: {str(e)}")


@router.get("/manager/{manager_id}", response_model=List[EmployeeResponse])
def get_direct_reports(
    manager_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all direct reports for a manager
    """
    try:
        # Verify manager exists
        manager = EmployeeService.get_employee(db, manager_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        employees = EmployeeService.get_employees_by_manager(db, manager_id)
        return [EmployeeResponse(**emp.to_dict()) for emp in employees]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get direct reports: {str(e)}")


@router.get("/search", response_model=List[EmployeeResponse])
def search_employees(
    q: str = Query(..., min_length=2, max_length=100, description="Search term"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    Search employees by name, email, or position
    """
    try:
        employees = EmployeeService.search_employees(db, q, limit)
        return [EmployeeResponse(**emp.to_dict()) for emp in employees]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/filter", response_model=EmployeeList)
def filter_employees(
    filter_params: EmployeeFilter,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Advanced employee filtering with multiple criteria
    """
    try:
        employees, total = EmployeeService.get_employees(db, skip, limit, filter_params)
        
        total_pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        return EmployeeList(
            items=[EmployeeResponse(**emp.to_dict()) for emp in employees],
            total=total,
            page=current_page,
            per_page=limit,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filtering failed: {str(e)}")


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific employee by ID
    """
    try:
        db_employee = EmployeeService.get_employee(db, employee_id)
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return EmployeeResponse(**db_employee.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve employee: {str(e)}")


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an employee with Pydantic validation
    """
    try:
        db_employee = EmployeeService.update_employee(db, employee_id, employee)
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return EmployeeResponse(**db_employee.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update employee: {str(e)}")


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete (terminate) an employee
    """
    try:
        success = EmployeeService.delete_employee(db, employee_id)
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete employee: {str(e)}")


# Bulk Operations
@router.post("/bulk", response_model=List[EmployeeResponse])
def bulk_create_employees(
    bulk_data: BulkEmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple employees in a single request
    """
    try:
        employees = EmployeeService.bulk_create_employees(db, bulk_data.employees)
        return [EmployeeResponse(**emp.to_dict()) for emp in employees]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk creation failed: {str(e)}")


@router.patch("/bulk-status", status_code=status.HTTP_200_OK)
def bulk_update_employee_status(
    bulk_update: BulkStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update status for multiple employees
    """
    try:
        updated_count = EmployeeService.bulk_update_status(
            db, bulk_update.employee_ids, bulk_update.status
        )
        return {"message": f"Updated {updated_count} employees", "updated_count": updated_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk status update failed: {str(e)}")


# Status Management Endpoints
@router.patch("/{employee_id}/activate", response_model=EmployeeResponse)
def activate_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Activate an employee (set status to ACTIVE)
    """
    try:
        update_data = EmployeeUpdate(status=EmployeeStatusEnum.ACTIVE)
        db_employee = EmployeeService.update_employee(db, employee_id, update_data)
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return EmployeeResponse(**db_employee.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate employee: {str(e)}")


@router.patch("/{employee_id}/deactivate", response_model=EmployeeResponse)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Deactivate an employee (set status to INACTIVE)
    """
    try:
        update_data = EmployeeUpdate(status=EmployeeStatusEnum.INACTIVE)
        db_employee = EmployeeService.update_employee(db, employee_id, update_data)
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return EmployeeResponse(**db_employee.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate employee: {str(e)}")