from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_preorder_batch_service, require_roles
from app.domain.roles import UserRole
from app.schemas.order import UserContext
from app.schemas.preorder_batch import PreorderBatchRead, PreorderSubmitRequest, SelectedPreorderSubmitRequest
from app.services.preorder_batch_service import PreorderBatchService

router = APIRouter(prefix="/client", tags=["preorders"])
ClientUser = Annotated[CurrentUser, Depends(require_roles(UserRole.CLIENT))]


@router.get("/preorders", response_model=list[PreorderBatchRead])
def list_client_preorders(
    current_user: ClientUser,
    service: Annotated[PreorderBatchService, Depends(get_preorder_batch_service)],
) -> list[PreorderBatchRead]:
    return service.list_for_client(current_user.id)


@router.post("/preorders/submit", response_model=PreorderBatchRead, status_code=201)
def submit_preorder_batch(
    payload: PreorderSubmitRequest,
    current_user: ClientUser,
    service: Annotated[PreorderBatchService, Depends(get_preorder_batch_service)],
) -> PreorderBatchRead:
    return service.submit(UserContext(id=current_user.id, role=current_user.role), payload)


@router.post("/preorders/submit-selected", response_model=PreorderBatchRead, status_code=201)
def submit_selected_preorder_batch(
    payload: SelectedPreorderSubmitRequest,
    current_user: ClientUser,
    service: Annotated[PreorderBatchService, Depends(get_preorder_batch_service)],
) -> PreorderBatchRead:
    return service.submit_selected(UserContext(id=current_user.id, role=current_user.role), payload)
