from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.content.carousel_layout import LayoutTemplate


class CarouselCover(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str
    subhead: str = ""


class CarouselSlide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str
    body: str
    visual_note: str = ""


class CarouselClosing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cta: str = ""


class CarouselData(BaseModel):
    """The carousel's re-editable structure -- stored as `Asset.body`
    (JSON) so the slide-by-slide editor can load it back exactly."""

    model_config = ConfigDict(extra="forbid")

    template: LayoutTemplate = "clean"
    cover: CarouselCover
    slides: list[CarouselSlide] = Field(min_length=1, max_length=12)
    closing: CarouselClosing = Field(default_factory=CarouselClosing)
    caption: str = ""


class SaveCarouselRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    data: CarouselData


class CarouselResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    data: CarouselData
