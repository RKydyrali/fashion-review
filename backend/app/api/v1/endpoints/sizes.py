from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import OptionalCurrentUser, get_size_chart_repository, get_size_recommendation_service
from app.repositories.size_chart_repository import SizeChartRepository
from app.schemas.sizing import BodyMeasurements, SizeChart, SizeRecommendationRequest, SizeRecommendationResponse
from app.services.size_recommendation_service import SizeRecommendationService

router = APIRouter(tags=["sizes"])


@router.post("/sizes/recommend", response_model=SizeRecommendationResponse)
def recommend_size(
    payload: SizeRecommendationRequest,
    current_user: OptionalCurrentUser,
    service: Annotated[SizeRecommendationService, Depends(get_size_recommendation_service)],
) -> SizeRecommendationResponse:
    measurements = _resolve_measurements(payload, current_user)
    return service.recommend_size(payload.model_copy(update={"measurements": measurements}))


@router.get("/size-charts/{chart_id}", response_model=SizeChart)
def get_size_chart(
    chart_id: int,
    repository: Annotated[SizeChartRepository, Depends(get_size_chart_repository)],
) -> SizeChart:
    chart = repository.get_by_id(chart_id)
    if chart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size chart not found")
    return chart


def _resolve_measurements(
    payload: SizeRecommendationRequest,
    current_user,
) -> BodyMeasurements:
    if payload.measurements is not None:
        return payload.measurements

    saved_measurements = None
    if current_user is not None and current_user.body_profile is not None:
        saved_measurements = current_user.body_profile.to_body_measurements()

    if saved_measurements is not None:
        return saved_measurements

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=(
            "measurements are required unless the authenticated user has saved "
            "chest_cm, waist_cm, and hips_cm values"
        ),
    )
