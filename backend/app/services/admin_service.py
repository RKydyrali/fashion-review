from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_password_hash
from app.models.bag_item import BagItem
from app.domain.language import LanguageCode
from app.domain.roles import UserRole
from app.models.branch import Branch
from app.models.collection import Collection
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.product import Product
from app.models.product_translation import ProductTranslation
from app.models.user import User
from app.schemas.admin import (
    AdminBranchSummary,
    AdminCollectionCreate,
    AdminCollectionRead,
    AdminCollectionTranslationInput,
    AdminCollectionTranslationsInput,
    AdminCollectionUpdate,
    AdminMediaUploadRead,
    AdminProductCreate,
    AdminProductRead,
    AdminProductTranslationInput,
    AdminProductTranslationsInput,
    AdminProductUpdate,
    AdminUserCreate,
    AdminUserRead,
    AdminUserUpdate,
)
from app.services.media_storage_service import LocalMediaStorageService


class AdminService:
    def __init__(self, session: Session, media_storage: LocalMediaStorageService) -> None:
        self.session = session
        self.media_storage = media_storage

    def list_users(self, query: str | None = None) -> list[AdminUserRead]:
        statement = select(User).order_by(User.id)
        normalized = query.strip().lower() if query else None
        if normalized:
            like = f"%{normalized}%"
            statement = statement.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
        branch_ids = self._branch_ids_by_manager()
        return [self._to_admin_user_read(user, branch_ids) for user in self.session.scalars(statement)]

    def list_branches(self) -> list[AdminBranchSummary]:
        return [
            AdminBranchSummary(
                id=branch.id,
                name=branch.name,
                code=branch.code,
                city=branch.city,
                manager_user_id=branch.manager_user_id,
            )
            for branch in self.session.scalars(select(Branch).order_by(Branch.id))
        ]

    def create_user(self, payload: AdminUserCreate) -> AdminUserRead:
        if payload.role == UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin accounts cannot be managed here")
        if self.session.scalar(select(User).where(User.email == str(payload.email)).limit(1)) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

        branch_id = self._validate_staff_role(role=payload.role, branch_id=payload.branch_id)
        user = User(
            email=str(payload.email),
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
            preferred_language=payload.preferred_language.value,
            is_active=True,
        )
        self.session.add(user)
        self.session.flush()
        self._assign_branch_manager(user.id, branch_id)
        self.session.commit()
        self.session.refresh(user)
        return self._to_admin_user_read(user, self._branch_ids_by_manager())

    def update_user(self, user_id: int, payload: AdminUserUpdate) -> AdminUserRead:
        user = self.session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.role == UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin accounts cannot be managed here")

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password is not None:
            user.hashed_password = get_password_hash(payload.password)
        if payload.preferred_language is not None:
            user.preferred_language = payload.preferred_language.value
        if payload.is_active is not None:
            user.is_active = payload.is_active

        next_role = payload.role or user.role
        current_branch_id = self._branch_ids_by_manager().get(user.id)
        requested_branch_id = payload.branch_id if (payload.role is not None or payload.branch_id is not None) else current_branch_id
        branch_id = self._validate_staff_role(role=next_role, branch_id=requested_branch_id)

        user.role = next_role
        self._clear_branch_manager_for_user(user.id)
        self._assign_branch_manager(user.id, branch_id)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return self._to_admin_user_read(user, self._branch_ids_by_manager())

    def list_products(self) -> list[AdminProductRead]:
        products = self.session.scalars(
            select(Product).options(selectinload(Product.translations)).order_by(Product.editorial_rank, Product.id)
        )
        return [self._to_admin_product_read(product) for product in products]

    def create_product(self, payload: AdminProductCreate) -> AdminProductRead:
        self._ensure_product_identifiers_available(payload.sku, payload.slug)
        self._ensure_collection_exists(payload.collection_slug)
        primary = payload.translations.en
        product = Product(
            sku=payload.sku,
            slug=payload.slug,
            name=primary.name,
            display_category=primary.display_category,
            normalized_category=payload.normalized_category,
            season_tags=payload.season_tags,
            color=payload.color,
            subtitle=primary.subtitle,
            long_description=primary.long_description,
            base_price_minor=payload.base_price_minor,
            currency=payload.currency.upper(),
            collection_slug=payload.collection_slug,
            hero_image_url=payload.hero_image_url,
            reference_image_url=payload.reference_image_url,
            gallery_image_urls=payload.gallery_image_urls,
            fabric_notes=primary.fabric_notes,
            care_notes=primary.care_notes,
            preorder_note=primary.preorder_note,
            available_sizes=payload.available_sizes,
            size_chart_id=payload.size_chart_id,
            editorial_rank=payload.editorial_rank,
            is_featured=payload.is_featured,
            is_available=payload.is_available,
            is_active=payload.is_active,
        )
        self.session.add(product)
        self.session.flush()
        self._replace_product_translations(product, payload.translations)
        self.session.commit()
        self.session.refresh(product)
        return self._to_admin_product_read(product)

    def update_product(self, product_id: int, payload: AdminProductUpdate) -> AdminProductRead:
        product = self._require_product(product_id)
        provided_fields = payload.model_fields_set
        if "sku" in provided_fields and payload.sku is not None and payload.sku != product.sku:
            self._ensure_product_identifiers_available(payload.sku, None, exclude_id=product.id)
            product.sku = payload.sku
        if "slug" in provided_fields and payload.slug is not None and payload.slug != product.slug:
            self._ensure_product_identifiers_available(None, payload.slug, exclude_id=product.id)
            product.slug = payload.slug
        if "collection_slug" in provided_fields:
            self._ensure_collection_exists(payload.collection_slug)
            product.collection_slug = payload.collection_slug

        for field_name in (
            "normalized_category",
            "season_tags",
            "color",
            "base_price_minor",
            "hero_image_url",
            "reference_image_url",
            "gallery_image_urls",
            "available_sizes",
            "editorial_rank",
            "is_featured",
            "is_available",
            "is_active",
        ):
            if field_name in provided_fields:
                setattr(product, field_name, getattr(payload, field_name))
        if "currency" in provided_fields and payload.currency is not None:
            product.currency = payload.currency.upper()
        if "size_chart_id" in provided_fields:
            product.size_chart_id = payload.size_chart_id
        if "translations" in provided_fields and payload.translations is not None:
            translations = {translation.language_code: translation for translation in product.translations}
            for language_code in ("en", "ru", "kk"):
                incoming = getattr(payload.translations, language_code)
                if incoming is None:
                    continue
                translation = translations.get(language_code)
                if translation is None:
                    translation = ProductTranslation(product_id=product.id, language_code=language_code)
                    self.session.add(translation)
                    product.translations.append(translation)
                self._apply_product_translation(translation, incoming)
            primary = translations.get("en") or next(iter(translations.values()))
            product.name = primary.name
            product.display_category = primary.display_category
            product.subtitle = primary.subtitle
            product.long_description = primary.long_description
            product.fabric_notes = primary.fabric_notes
            product.care_notes = primary.care_notes
            product.preorder_note = primary.preorder_note
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return self._to_admin_product_read(product)

    def archive_product(self, product_id: int) -> AdminProductRead:
        product = self._require_product(product_id)
        product.is_active = False
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return self._to_admin_product_read(product)

    def restore_product(self, product_id: int) -> AdminProductRead:
        product = self._require_product(product_id)
        product.is_active = True
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return self._to_admin_product_read(product)

    def permanently_delete_product(self, product_id: int) -> None:
        product = self._require_product(product_id)
        has_orders = self.session.scalar(select(Order.id).where(Order.product_id == product_id).limit(1)) is not None
        if has_orders:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Products with order history cannot be deleted permanently",
            )

        for favorite in self.session.scalars(select(Favorite).where(Favorite.product_id == product_id)):
            self.session.delete(favorite)
        for bag_item in self.session.scalars(select(BagItem).where(BagItem.product_id == product_id)):
            self.session.delete(bag_item)
        self.session.delete(product)
        self.session.commit()
        return None

    def list_collections(self) -> list[AdminCollectionRead]:
        return [
            self._to_admin_collection_read(collection)
            for collection in self.session.scalars(select(Collection).order_by(Collection.sort_order, Collection.id))
        ]

    def create_collection(self, payload: AdminCollectionCreate) -> AdminCollectionRead:
        existing = self.session.scalar(select(Collection).where(Collection.slug == payload.slug).limit(1))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Collection slug already exists")
        collection = Collection(
            slug=payload.slug,
            hero_image_url=payload.hero_image_url,
            cover_image_url=payload.cover_image_url,
            sort_order=payload.sort_order,
            is_featured=payload.is_featured,
            is_active=payload.is_active,
            name_translations=self._collection_names(payload.translations),
            summary_translations=self._collection_summaries(payload.translations),
            eyebrow_translations=self._collection_eyebrows(payload.translations),
        )
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return self._to_admin_collection_read(collection)

    def update_collection(self, collection_id: int, payload: AdminCollectionUpdate) -> AdminCollectionRead:
        collection = self._require_collection(collection_id)
        provided_fields = payload.model_fields_set
        if "slug" in provided_fields and payload.slug is not None and payload.slug != collection.slug:
            existing = self.session.scalar(select(Collection).where(Collection.slug == payload.slug).limit(1))
            if existing is not None and existing.id != collection_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Collection slug already exists")
            previous_slug = collection.slug
            collection.slug = payload.slug
            for product in self.session.scalars(select(Product).where(Product.collection_slug == previous_slug)):
                product.collection_slug = payload.slug
                self.session.add(product)
        if "hero_image_url" in provided_fields and payload.hero_image_url is not None:
            collection.hero_image_url = payload.hero_image_url
        if "cover_image_url" in provided_fields and payload.cover_image_url is not None:
            collection.cover_image_url = payload.cover_image_url
        if "sort_order" in provided_fields and payload.sort_order is not None:
            collection.sort_order = payload.sort_order
        if "is_featured" in provided_fields and payload.is_featured is not None:
            collection.is_featured = payload.is_featured
        if "is_active" in provided_fields and payload.is_active is not None:
            collection.is_active = payload.is_active
        if "translations" in provided_fields and payload.translations is not None:
            name_translations = dict(collection.name_translations)
            summary_translations = dict(collection.summary_translations)
            eyebrow_translations = dict(collection.eyebrow_translations)
            for language_code in ("en", "ru", "kk"):
                incoming = getattr(payload.translations, language_code)
                if incoming is None:
                    continue
                name_translations[language_code] = incoming.title
                summary_translations[language_code] = incoming.summary
                eyebrow_translations[language_code] = incoming.eyebrow
            collection.name_translations = name_translations
            collection.summary_translations = summary_translations
            collection.eyebrow_translations = eyebrow_translations
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return self._to_admin_collection_read(collection)

    def archive_collection(self, collection_id: int) -> AdminCollectionRead:
        collection = self._require_collection(collection_id)
        collection.is_active = False
        for product in self.session.scalars(select(Product).where(Product.collection_slug == collection.slug)):
            product.collection_slug = None
            self.session.add(product)
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return self._to_admin_collection_read(collection)

    def restore_collection(self, collection_id: int) -> AdminCollectionRead:
        collection = self._require_collection(collection_id)
        collection.is_active = True
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        return self._to_admin_collection_read(collection)

    def store_catalog_media(self, *, entity: str, slot: str, filename: str, content: bytes) -> AdminMediaUploadRead:
        relative_path = self.media_storage.save_catalog_upload(entity=entity, slot=slot, filename=filename, content=content)
        return AdminMediaUploadRead(url=self.media_storage.url_for(relative_path) or "", relative_path=relative_path)

    def _branch_ids_by_manager(self) -> dict[int, int]:
        return {
            branch.manager_user_id: branch.id
            for branch in self.session.scalars(select(Branch).where(Branch.manager_user_id.is_not(None)))
            if branch.manager_user_id is not None
        }

    def _to_admin_user_read(self, user: User, branch_ids: dict[int, int]) -> AdminUserRead:
        language = user.preferred_language if isinstance(user.preferred_language, LanguageCode) else LanguageCode(user.preferred_language)
        return AdminUserRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            preferred_language=language,
            is_active=user.is_active,
            branch_id=branch_ids.get(user.id),
        )

    def _validate_staff_role(self, *, role: UserRole, branch_id: int | None) -> int | None:
        if role == UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin accounts cannot be managed here")
        if role == UserRole.FRANCHISEE:
            if branch_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Franchisee requires a branch assignment")
            self._require_branch(branch_id)
            return branch_id
        if branch_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only franchisees can have branch assignments")
        return None

    def _assign_branch_manager(self, user_id: int, branch_id: int | None) -> None:
        if branch_id is None:
            return
        branch = self._require_branch(branch_id)
        branch.manager_user_id = user_id
        self.session.add(branch)

    def _clear_branch_manager_for_user(self, user_id: int) -> None:
        released_branches = list(self.session.scalars(select(Branch).where(Branch.manager_user_id == user_id)))
        for branch in released_branches:
            branch.manager_user_id = None
            self.session.add(branch)
        for branch in released_branches:
            replacement = self._find_unassigned_franchisee(exclude_user_id=user_id)
            if replacement is None:
                continue
            branch.manager_user_id = replacement.id
            self.session.add(branch)

    def _require_branch(self, branch_id: int) -> Branch:
        branch = self.session.get(Branch, branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        return branch

    def _find_unassigned_franchisee(self, *, exclude_user_id: int) -> User | None:
        assigned_user_ids = {
            branch.manager_user_id
            for branch in self.session.scalars(select(Branch).where(Branch.manager_user_id.is_not(None)))
            if branch.manager_user_id is not None
        }
        statement = (
            select(User)
            .where(
                User.role == UserRole.FRANCHISEE,
                User.id != exclude_user_id,
                User.id.not_in(assigned_user_ids) if assigned_user_ids else True,
            )
            .order_by(User.id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def _ensure_product_identifiers_available(self, sku: str | None, slug: str | None, exclude_id: int | None = None) -> None:
        if sku is not None:
            existing_sku = self.session.scalar(select(Product).where(Product.sku == sku).limit(1))
            if existing_sku is not None and existing_sku.id != exclude_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")
        if slug is not None:
            existing_slug = self.session.scalar(select(Product).where(Product.slug == slug).limit(1))
            if existing_slug is not None and existing_slug.id != exclude_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    def _ensure_collection_exists(self, collection_slug: str | None) -> None:
        if collection_slug is None:
            return
        collection = self.session.scalar(select(Collection).where(Collection.slug == collection_slug).limit(1))
        if collection is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    def _replace_product_translations(self, product: Product, translations: AdminProductTranslationsInput) -> None:
        for language_code in ("en", "ru", "kk"):
            translation = ProductTranslation(product_id=product.id, language_code=language_code)
            self._apply_product_translation(translation, getattr(translations, language_code))
            self.session.add(translation)

    def _apply_product_translation(self, translation: ProductTranslation, payload: AdminProductTranslationInput) -> None:
        translation.name = payload.name
        translation.description = payload.description
        translation.subtitle = payload.subtitle
        translation.long_description = payload.long_description
        translation.fabric_notes = payload.fabric_notes
        translation.care_notes = payload.care_notes
        translation.preorder_note = payload.preorder_note
        translation.display_category = payload.display_category

    def _require_product(self, product_id: int) -> Product:
        product = self.session.scalar(select(Product).options(selectinload(Product.translations)).where(Product.id == product_id).limit(1))
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def _product_translation_input(self, translation: ProductTranslation) -> AdminProductTranslationInput:
        return AdminProductTranslationInput(
            name=translation.name,
            description=translation.description,
            subtitle=translation.subtitle,
            long_description=translation.long_description,
            fabric_notes=translation.fabric_notes,
            care_notes=translation.care_notes,
            preorder_note=translation.preorder_note,
            display_category=translation.display_category,
        )

    def _to_admin_product_read(self, product: Product) -> AdminProductRead:
        translations = {translation.language_code: translation for translation in product.translations}
        return AdminProductRead(
            id=product.id,
            sku=product.sku,
            slug=product.slug,
            normalized_category=product.normalized_category,
            season_tags=list(product.season_tags),
            color=product.color,
            base_price_minor=product.base_price_minor,
            currency=product.currency,
            collection_slug=product.collection_slug,
            hero_image_url=product.hero_image_url,
            reference_image_url=product.reference_image_url,
            gallery_image_urls=list(product.gallery_image_urls),
            available_sizes=list(product.available_sizes),
            size_chart_id=product.size_chart_id,
            editorial_rank=product.editorial_rank,
            is_featured=product.is_featured,
            is_available=product.is_available,
            is_active=product.is_active,
            translations=AdminProductTranslationsInput(
                en=self._product_translation_input(translations["en"]),
                ru=self._product_translation_input(translations["ru"]),
                kk=self._product_translation_input(translations["kk"]),
            ),
        )

    def _collection_names(self, translations: AdminCollectionTranslationsInput) -> dict[str, str]:
        return {language: getattr(translations, language).title for language in ("en", "ru", "kk")}

    def _collection_summaries(self, translations: AdminCollectionTranslationsInput) -> dict[str, str]:
        return {language: getattr(translations, language).summary for language in ("en", "ru", "kk")}

    def _collection_eyebrows(self, translations: AdminCollectionTranslationsInput) -> dict[str, str]:
        return {language: getattr(translations, language).eyebrow for language in ("en", "ru", "kk")}

    def _require_collection(self, collection_id: int) -> Collection:
        collection = self.session.get(Collection, collection_id)
        if collection is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
        return collection

    def _collection_translation_input(self, collection: Collection, language_code: str) -> AdminCollectionTranslationInput:
        return AdminCollectionTranslationInput(
            title=collection.name_translations.get(language_code, ""),
            summary=collection.summary_translations.get(language_code, ""),
            eyebrow=collection.eyebrow_translations.get(language_code, ""),
        )

    def _to_admin_collection_read(self, collection: Collection) -> AdminCollectionRead:
        return AdminCollectionRead(
            id=collection.id,
            slug=collection.slug,
            hero_image_url=collection.hero_image_url,
            cover_image_url=collection.cover_image_url,
            sort_order=collection.sort_order,
            is_featured=collection.is_featured,
            is_active=collection.is_active,
            translations=AdminCollectionTranslationsInput(
                en=self._collection_translation_input(collection, "en"),
                ru=self._collection_translation_input(collection, "ru"),
                kk=self._collection_translation_input(collection, "kk"),
            ),
        )
