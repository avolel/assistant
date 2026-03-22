from fastapi import APIRouter, HTTPException
from ..models import SetupRequest, IdentityResponse, UpdateNameRequest, AddOwnerRequest, OwnerInfo
from ...core.identity import IdentityManager

router = APIRouter()
identity_manager = IdentityManager()


def _to_response(identity) -> IdentityResponse:
    owners = [OwnerInfo(owner_id=o.owner_id, name=o.name, email=o.email) for o in identity.owners]
    return IdentityResponse(
        assistant_name=identity.name,
        owner_name=identity.owners[0].name if identity.owners else "",
        owners=owners,
        configured=True,
    )


@router.get("/", response_model=IdentityResponse)
async def get_identity():
    if not identity_manager.is_configured():
        return IdentityResponse(assistant_name="", owner_name="", owners=[], configured=False)
    return _to_response(identity_manager.load())


@router.post("/setup", response_model=IdentityResponse)
async def setup_identity(req: SetupRequest):
    if identity_manager.is_configured():
        raise HTTPException(400, "Already configured")
    identity = identity_manager.setup(req.assistant_name, req.owner_name, req.owner_email, req.timezone)
    return _to_response(identity)


@router.patch("/", response_model=IdentityResponse)
async def update_name(req: UpdateNameRequest):
    if not identity_manager.is_configured():
        raise HTTPException(400, "Not configured")
    if not req.assistant_name.strip():
        raise HTTPException(422, "Name cannot be empty")
    identity = identity_manager.update_name(req.assistant_name.strip())
    return _to_response(identity)


@router.post("/owners", response_model=IdentityResponse)
async def add_owner(req: AddOwnerRequest):
    if not identity_manager.is_configured():
        raise HTTPException(400, "Not configured")
    if not req.name.strip():
        raise HTTPException(422, "Owner name cannot be empty")
    identity = identity_manager.add_owner(req.name.strip(), req.email, req.timezone)
    return _to_response(identity)


@router.delete("/owners/{owner_id}", response_model=IdentityResponse)
async def remove_owner(owner_id: str):
    if not identity_manager.is_configured():
        raise HTTPException(400, "Not configured")
    try:
        identity = identity_manager.remove_owner(owner_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _to_response(identity)