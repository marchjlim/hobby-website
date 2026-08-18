import math

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from auth import require_admin


router = APIRouter(prefix="/api/products", tags=["products"])
PAGE_SIZE = 200


@router.get("")
def get_products(
    page: int = Query(default=1, ge=1),
    q: str = Query(default="", max_length=100),
    authenticated_supabase: Client = Depends(require_admin),
):
    start = (page - 1) * PAGE_SIZE
    try:
        query = (
            authenticated_supabase.table("products")
            .select("*", count="exact")
            .order("canonical_name")
        )
        if q := q.strip():
            query = query.ilike("canonical_name", f"%{q}%")
        response = query.range(start, start + PAGE_SIZE - 1).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to fetch products") from exc

    total = response.count or 0
    return {
        "results": response.data,
        "page": page,
        "page_size": PAGE_SIZE,
        "total": total,
        "total_pages": math.ceil(total / PAGE_SIZE),
    }
