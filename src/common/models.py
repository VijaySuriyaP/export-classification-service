"""Typed API and agent contracts."""
from __future__ import annotations

import os
import re
from enum import Enum
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ISO_ALPHA2 = set("AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW".split())


class Material(str, Enum):
    STAINLESS_STEEL = "stainless_steel"
    CARBON_STEEL = "carbon_steel"
    ALLOY_STEEL = "alloy_steel"
    IRON = "iron"
    ALUMINIUM = "aluminium"
    PLASTIC = "plastic"
    WOOD = "wood"
    TEXTILE = "textile"
    GLASS = "glass"
    CERAMIC = "ceramic"
    PAPER = "paper"
    OTHER = "other"
    UNKNOWN = "unknown"


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"


class Route(str, Enum):
    CLEAR_FOR_FILING = "clear-for-filing"
    SEEK_PRODUCT_CLARIFICATION = "seek-product-clarification"
    SPECIALIST_CLASSIFICATION_REVIEW = "specialist-classification-review"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED_ESCALATED = "failed_escalated"


class ClassifyRequest(BaseModel):
    """Validated data required to start a classification check."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    client_request_id: UUID
    product_description: str = Field(min_length=10, max_length=2000)
    materials: list[Material] = Field(min_length=1, max_length=12)
    intended_use: str | None = Field(default=None, max_length=1000)
    weight_grams: float | None = Field(default=None, gt=0, le=1_000_000_000)
    unit_value: float | None = Field(default=None, gt=0, le=1_000_000_000)
    currency: Currency | None = None
    destination_country: str
    hs_hint: str | None = None
    callback_url: str | None = None
    client_id: str = Field(min_length=1, max_length=128)

    @field_validator("destination_country")
    @classmethod
    def valid_country_code(cls, value: str) -> str:
        if value not in ISO_ALPHA2:
            raise ValueError("must be a valid uppercase ISO-3166 alpha-2 code")
        return value

    @field_validator("hs_hint")
    @classmethod
    def valid_hs_hint(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(r"\d{2,10}", value):
                raise ValueError("must contain 2 to 10 digits")
            chapter = int(value[:2])
            if not 1 <= chapter <= 97:
                raise ValueError("chapter must be a valid two-digit chapter number")
        return value

    @field_validator("callback_url")
    @classmethod
    def allowlisted_https_callback(cls, value: str | None) -> str | None:
        if not value:
            return value
        parsed = urlparse(value)
        allowlist = [x.strip().lower() for x in os.getenv("CALLBACK_ALLOWLIST", "").split(",") if x.strip()]
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not host or not allowlist:
            raise ValueError("callback_url must be HTTPS and its host must be allowlisted")
        if not any(host == item or host.endswith("." + item) for item in allowlist):
            raise ValueError("callback_url host is not allowlisted")
        return value

    @model_validator(mode="after")
    def cross_field_rules(self) -> "ClassifyRequest":
        if self.unit_value is not None and self.currency is None:
            raise ValueError("currency is required when unit_value is supplied")
        return self


class Citation(BaseModel):
    chunk_id: str
    identifier: str
    doc: str
    page: int | None = None
    excerpt: str


class HandoffPayload(BaseModel):
    run_id: str
    request: dict[str, Any]
    proposed_hs_code: str | None = None
    rule_applied: str | None = None
    route: Route
    basis: str
    citations: list[Citation] = Field(default_factory=list)
    passages: list[dict[str, Any]] = Field(default_factory=list)
    export_policy: dict[str, Any] | None = None
    prompt_version: str = "v1"
    degraded: bool = False
    trace: list[dict[str, Any]] = Field(default_factory=list)
