from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.crud import measurement as measurement_crud

router = APIRouter(prefix="/measurements", tags=["measurements"])

@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Poista yksittäinen mittaus",
               description="Poistaa virheellisen mittaustuloksen tietokannasta ID:n perusteella.")
async def delete_measurement(
    measurement_id: int,
    session: AsyncSession = Depends(get_session)
):
    success = await measurement_crud.delete_measurement(session, measurement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    return None