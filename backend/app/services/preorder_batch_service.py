from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.roles import UserRole
from app.repositories.preorder_batch_repository import PreorderBatchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import OrderCreate, UserContext
from app.schemas.preorder_batch import PreorderBatchRead, PreorderSubmitRequest, SelectedPreorderSubmitRequest
from app.services.bag_service import BagService
from app.services.order_service import OrderService
from app.services.product_localization import money


FIRST_ORDER_DISCOUNT = 0.05


class PreorderBatchService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.bag_service = BagService(session)
        self.order_service = OrderService(session)
        self.repository = PreorderBatchRepository(session)
        self.user_repository = UserRepository(session)

    def submit(self, current_user: UserContext, payload: PreorderSubmitRequest) -> PreorderBatchRead:
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can submit preorders")
        bag_items = self.bag_service.get_models_for_user(current_user.id)
        if not bag_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bag is empty")

        return self._submit_bag_items(current_user, payload.delivery_city, bag_items, clear_full_bag=True)

    def submit_selected(self, current_user: UserContext, payload: SelectedPreorderSubmitRequest) -> PreorderBatchRead:
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can submit preorders")

        selected_ids = list(dict.fromkeys(payload.bag_item_ids))
        bag_items = self.bag_service.get_models_for_user_by_ids(current_user.id, selected_ids)
        if not bag_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selected bag items found")
        if len(bag_items) != len(selected_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Some selected bag items were not found")

        return self._submit_bag_items(current_user, payload.delivery_city, bag_items, clear_full_bag=False)

    def _submit_bag_items(
        self,
        current_user: UserContext,
        delivery_city: str | None,
        bag_items,
        *,
        clear_full_bag: bool,
    ) -> PreorderBatchRead:
        currency = bag_items[0].currency
        total_minor = sum(item.line_total_minor for item in bag_items)
        
        user = self.user_repository.get_by_id(current_user.id)
        discount_applied_minor = 0
        discount_percentage = 0
        
        if user and not user.first_order_discount_used:
            discount_applied_minor = int(total_minor * FIRST_ORDER_DISCOUNT)
            discount_percentage = int(FIRST_ORDER_DISCOUNT * 100)
            user.first_order_discount_used = True
            self.session.add(user)
        
        discounted_total_minor = total_minor - discount_applied_minor
        
        batch = self.repository.create(
            client_id=current_user.id,
            delivery_city=delivery_city,
            item_count=len(bag_items),
            total_price_minor=discounted_total_minor,
            currency=currency,
        )
        orders = []
        for item in bag_items:
            orders.append(
                self.order_service.create_order(
                    current_user,
                    OrderCreate(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        delivery_city=delivery_city,
                        size_label=item.size_label,
                        preorder_batch_id=batch.id,
                    ),
                )
            )
        if clear_full_bag:
            self.bag_service.bag.clear_for_user(current_user.id)
        else:
            self.bag_service.delete_items_for_user(current_user.id, [item.id for item in bag_items])
        self.session.commit()
        
        return PreorderBatchRead(
            id=batch.id,
            client_id=batch.client_id,
            delivery_city=batch.delivery_city,
            item_count=batch.item_count,
            total_price=money(discounted_total_minor, currency),
            original_price=money(total_minor, currency) if discount_applied_minor > 0 else None,
            discount_applied=money(discount_applied_minor, currency) if discount_applied_minor > 0 else None,
            discount_percentage=discount_percentage if discount_percentage > 0 else None,
            currency=batch.currency,
            status=batch.status,
            created_at=batch.created_at,
            orders=orders,
        )

    def list_for_client(self, client_id: int) -> list[PreorderBatchRead]:
        batches = self.repository.list_for_client(client_id)
        return [
            PreorderBatchRead(
                id=batch.id,
                client_id=batch.client_id,
                delivery_city=batch.delivery_city,
                item_count=batch.item_count,
                total_price=money(batch.total_price_minor, batch.currency),
                currency=batch.currency,
                status=batch.status,
                created_at=batch.created_at,
                orders=[self.order_service.serialize_order(order) for order in batch.orders],
            )
            for batch in batches
        ]
