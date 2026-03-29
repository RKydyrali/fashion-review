from app.core.enums import PreorderLifecycle
from app.schemas.preorder import PreorderCreate, PreorderRead


class PreorderRepository:
    def __init__(self) -> None:
        self._preorders: list[PreorderRead] = []
        self._next_id = 1

    def create(self, payload: PreorderCreate) -> PreorderRead:
        preorder = PreorderRead(
            id=self._next_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            requested_by_user_id=payload.requested_by_user_id,
            status=PreorderLifecycle.CREATED,
        )
        self._preorders.append(preorder)
        self._next_id += 1
        return preorder

    def list_all(self) -> list[PreorderRead]:
        return list(self._preorders)

    def get_by_id(self, preorder_id: int) -> PreorderRead | None:
        return next((item for item in self._preorders if item.id == preorder_id), None)

    def update(self, preorder: PreorderRead) -> PreorderRead:
        for index, item in enumerate(self._preorders):
            if item.id == preorder.id:
                self._preorders[index] = preorder
                return preorder

        self._preorders.append(preorder)
        return preorder
