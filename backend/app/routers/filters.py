from fastapi import APIRouter

from app import queries
from app.db import SessionDep
from app.schemas import FilterOptions

router = APIRouter(tags=["applications"])


@router.get("/filter-options", response_model=FilterOptions)
def filter_options(session: SessionDep):
    countries, job_families = queries.distinct_job_values(session)
    return FilterOptions(countries=countries, job_families=job_families)
