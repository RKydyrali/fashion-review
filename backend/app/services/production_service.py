from app.core.enums import PreorderLifecycle
from app.schemas.preorder import PreorderRead


class ProductionService:
    def mark_in_production(self, preorder: PreorderRead) -> PreorderRead:
        return preorder.model_copy(update={"status": PreorderLifecycle.IN_PRODUCTION})
