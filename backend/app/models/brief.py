from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectBrief(BaseModel):
    client_name_or_business: str = Field(
        default="Unknown Prospect", description="Name of company or client"
    )
    business_type: str = Field(
        ..., description="Industry, type of business, or current stage"
    )
    current_situation: str = Field(
        ..., description="Existing website, tech stack, or lack thereof"
    )
    goals_and_needs: List[str] = Field(
        default_factory=list, description="Primary goals, features, or pain points"
    )
    suggested_service_category: str = Field(
        ...,
        description="Suggested TIQC category: e.g. Custom Web App, Site Redesign, E-commerce, MVP Build",
    )
    rough_budget_range: Optional[str] = Field(
        default="Not specified", description="Stated or estimated budget tier"
    )
    target_timeline: Optional[str] = Field(
        default="Not specified", description="Desired launch date or urgency"
    )
    flagged_unknowns: List[str] = Field(
        default_factory=list,
        description="Key gaps, open questions, or ambiguities for staff discovery call",
    )