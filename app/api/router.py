"""Central API router - mounts all sub-routers."""
from fastapi import APIRouter

from app.api.employees import router as employees_router
from app.api.departments import router as departments_router
from app.api.schedules import router as schedules_router
from app.api.shifts import router as shifts_router
from app.api.simulation import router as simulation_router
from app.api.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(auth_router,       prefix="/auth",        tags=["Auth"])
api_router.include_router(employees_router,  prefix="/employees",   tags=["Employees"])
api_router.include_router(departments_router,prefix="/departments",  tags=["Departments"])
api_router.include_router(schedules_router,  prefix="/schedules",   tags=["Schedules"])
api_router.include_router(shifts_router,     prefix="/shifts",      tags=["Shifts"])
api_router.include_router(simulation_router, prefix="/simulate",    tags=["Simulation"])
