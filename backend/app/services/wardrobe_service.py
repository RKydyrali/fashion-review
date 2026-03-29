from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from app.domain.language import DEFAULT_LANGUAGE, LanguageCode
from app.domain.product_taxonomy import NEUTRAL_COLORS
from app.repositories.product_repository import ProductRepository
from app.schemas.wardrobe import (
    CapsuleOutfitRead,
    CapsuleWardrobeRequest,
    CapsuleWardrobeResponse,
    WardrobeCatalogItemInput,
    WardrobeItemRead,
)
from app.services.product_localization import to_wardrobe_item_read


@dataclass(frozen=True)
class OutfitCandidate:
    items: tuple[WardrobeItemRead, ...]
    colors: tuple[str, ...]
    neutral_score: int
    has_outerwear: bool
    skus: tuple[str, ...]


class WardrobeService:
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository
        self.default_language = DEFAULT_LANGUAGE

    def generate_capsule(
        self,
        request: CapsuleWardrobeRequest,
        language: LanguageCode = DEFAULT_LANGUAGE,
    ) -> CapsuleWardrobeResponse:
        candidates = self._filter_candidates(self._load_source_items(request, language), request)
        grouped = self._group_candidates(candidates)
        if not grouped["top"] or not grouped["bottom"]:
            return CapsuleWardrobeResponse(
                capsule_items=[],
                outfits=[],
                summary="No capsule could be built from the filtered candidate set.",
            )

        outfits = self._build_outfits(grouped, request)
        if not outfits:
            return CapsuleWardrobeResponse(
                capsule_items=[],
                outfits=[],
                summary="No capsule could be built from the filtered candidate set.",
            )

        capsule_items = self._build_capsule_items(outfits)
        summary = (
            f"Built {len(outfits)} outfit combinations from {len(capsule_items)} reusable items "
            "with a restrained minimal-luxury palette."
        )
        return CapsuleWardrobeResponse(
            capsule_items=capsule_items,
            outfits=outfits,
            summary=summary,
        )

    def _load_source_items(
        self,
        request: CapsuleWardrobeRequest,
        language: LanguageCode,
    ) -> list[WardrobeItemRead]:
        if request.catalog is not None:
            return [self._to_item_read(item) for item in request.catalog]
        if self.repository is None:
            return []
        stored_products = self.repository.list_all()
        return [
            to_wardrobe_item_read(product, language, fallback_language=self.default_language)
            for product in stored_products
        ]

    def _filter_candidates(
        self,
        items: list[WardrobeItemRead],
        request: CapsuleWardrobeRequest,
    ) -> list[WardrobeItemRead]:
        allowed_categories = set(request.allowed_categories)
        requested_season = request.season.casefold()
        return [
            item
            for item in items
            if item.is_active
            and item.is_available
            and item.normalized_category in allowed_categories
            and any(tag.casefold() == requested_season for tag in item.season_tags)
        ]

    def _group_candidates(self, items: list[WardrobeItemRead]) -> dict[str, list[WardrobeItemRead]]:
        grouped = {"top": [], "bottom": [], "outerwear": []}
        for item in items:
            grouped[item.normalized_category].append(item)
        for key in grouped:
            grouped[key].sort(key=self._item_sort_key)
        return grouped

    def _build_outfits(
        self,
        grouped: dict[str, list[WardrobeItemRead]],
        request: CapsuleWardrobeRequest,
    ) -> list[CapsuleOutfitRead]:
        outerwear_options: list[WardrobeItemRead | None] = [None]
        if "outerwear" in request.allowed_categories and grouped["outerwear"]:
            outerwear_options.extend(grouped["outerwear"])

        candidates: list[OutfitCandidate] = []
        for top, bottom, outerwear in product(grouped["top"], grouped["bottom"], outerwear_options):
            items = tuple(item for item in (top, bottom, outerwear) if item is not None)
            colors = tuple(dict.fromkeys(item.color for item in items))
            if len(colors) > 3:
                continue
            candidates.append(
                OutfitCandidate(
                    items=items,
                    colors=colors,
                    neutral_score=sum(1 for item in items if item.color in NEUTRAL_COLORS),
                    has_outerwear=outerwear is not None,
                    skus=tuple(item.sku for item in items),
                )
            )

        selected: list[OutfitCandidate] = []
        capsule_ids: set[int] = set()
        while len(selected) < request.max_outfits:
            viable = []
            for candidate in candidates:
                if candidate in selected:
                    continue
                candidate_ids = {item.id for item in candidate.items}
                combined_ids = capsule_ids | candidate_ids
                if len(combined_ids) > request.target_item_limit:
                    continue
                overlap = len(capsule_ids & candidate_ids)
                viable.append(
                    (
                        candidate,
                        overlap,
                        len(candidate.colors),
                        len(combined_ids - capsule_ids),
                    )
                )

            if not viable:
                break

            viable.sort(
                key=lambda row: (
                    -(row[1] if selected else 0),
                    -row[0].neutral_score,
                    row[2],
                    row[3],
                    -int(row[0].has_outerwear),
                    row[0].skus,
                )
            )
            winner = viable[0][0]
            selected.append(winner)
            capsule_ids.update(item.id for item in winner.items)

        return [
            CapsuleOutfitRead(
                items=list(candidate.items),
                colors=list(candidate.colors),
                explanation=self._build_explanation(candidate),
            )
            for candidate in selected
        ]

    def _build_capsule_items(self, outfits: list[CapsuleOutfitRead]) -> list[WardrobeItemRead]:
        unique_items: dict[int, WardrobeItemRead] = {}
        for outfit in outfits:
            for item in outfit.items:
                unique_items[item.id] = item
        return sorted(unique_items.values(), key=self._item_sort_key)

    def _build_explanation(self, candidate: OutfitCandidate) -> str:
        color_text = ", ".join(candidate.colors)
        outerwear_text = ""
        if candidate.has_outerwear:
            outerwear_text = " The outerwear layer keeps the silhouette polished and quiet."
        return (
            f"This look stays refined through a controlled palette of {color_text}, "
            "balancing clean proportions and soft texture contrast for a minimal luxury feel."
            f"{outerwear_text}"
        )

    def _to_item_read(self, item: WardrobeCatalogItemInput) -> WardrobeItemRead:
        return WardrobeItemRead.model_validate(item.model_dump())

    def _item_sort_key(self, item: WardrobeItemRead) -> tuple[int, str, str]:
        return (0 if item.color in NEUTRAL_COLORS else 1, item.sku, item.name)
