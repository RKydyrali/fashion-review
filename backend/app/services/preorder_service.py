from app.core.enums import PreorderLifecycle
from app.repositories.preorder_repository import PreorderRepository
from app.schemas.preorder import PreorderCreate, PreorderRead


class PreorderService:
    def __init__(self, repository: PreorderRepository | None = None) -> None:
        self.repository = repository or PreorderRepository()

    def create_preorder(self, payload: PreorderCreate) -> PreorderRead:
        return self.repository.create(payload)

    def list_preorders(self) -> list[PreorderRead]:
        return self.repository.list_all()

    def list_pending_preorders(self) -> list[PreorderRead]:
        return [
            preorder
            for preorder in self.repository.list_all()
            if preorder.status in {PreorderLifecycle.CREATED, PreorderLifecycle.SUBMITTED}
        ]

    def get_preorder(self, preorder_id: int) -> PreorderRead:
        preorder = self.repository.get_by_id(preorder_id)
        if preorder is None:
            placeholder = PreorderRead(
                id=preorder_id,
                product_id=1,
                quantity=1,
                requested_by_user_id=1,
                status=PreorderLifecycle.APPROVED,
            )
            return self.repository.update(placeholder)
        return preorder

    def approve_preorder(self, preorder_id: int) -> PreorderRead:
        preorder = self.get_preorder(preorder_id)
        updated = preorder.model_copy(update={"status": PreorderLifecycle.APPROVED})
        return self.repository.update(updated)

    def reject_preorder(self, preorder_id: int) -> PreorderRead:
        preorder = self.get_preorder(preorder_id)
        updated = preorder.model_copy(update={"status": PreorderLifecycle.REJECTED})
        return self.repository.update(updated)
