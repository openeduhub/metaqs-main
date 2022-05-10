from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import PERCENTAGE_DESCRIPTOR


class ColumnOutput(BaseModel):
    metadatum: str = Field(default="", description="Name of the evaluated metadatum.")
    bpb_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    br_rss_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    geogebra_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    oai_sodis_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    rpi_virtuell_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    serlo_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    tutory_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
    youtube_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    zum_klexikon_spider: Optional[float] = Field(
        default=0, description=PERCENTAGE_DESCRIPTOR
    )
    zum_spider: Optional[float] = Field(default=0, description=PERCENTAGE_DESCRIPTOR)
