from enum import Enum


class OrderDeadlineStage(str, Enum):
    BRANCH_REVIEW = "branch_review"
    PRODUCTION_START = "production_start"
    PRODUCTION_COMPLETION = "production_completion"
