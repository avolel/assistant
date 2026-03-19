from fastapi import APIRouter, HTTPException
from ..models import SetupRequest, IdentityResponse
from ...core.identity import IdentityManager

router = APIRouter()
identity_manager = IdentityManager()

@router.get("/", response_model=IdentityResponse)
async def get_identity():
    if not identity_manager.is_configured():
        return IdentityResponse(assistant_name="",owner_name="",configured=False)
    identity = identity_manager.load()
    return IdentityResponse(
        assistant_name=identity.name,
        owner_name=identity.owners[0].name if identity.owners else "",
        configured=True
    )

@router.post("/setup", response_model=IdentityResponse)
async def setup_identity(req: SetupRequest):
    if identity_manager.is_configured():
        raise HTTPException(400, "Already configured")
    identity = identity_manager.setup(req.assistant_name,req.owner_name,req.owner_email,req.timezone)
    return IdentityResponse(assistant_name=identity.name,
                            owner_name=identity.owners[0].name,
                            configured=True)