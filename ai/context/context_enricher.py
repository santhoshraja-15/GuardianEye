"""
Context Enrichment Engine for GuardianEye
Associates product fragility, SKU metadata, zone risk profiles, and operational parameters with detected behaviour events.
"""
import dataclasses
from dataclasses import dataclass
from typing import Dict, Optional

from ai.context.product_catalog import (
    CLASS_DEFAULT_PROFILES,
    DEMO_SKU_CATALOG,
    GENERIC_FALLBACK_PROFILE,
    ProductContext,
)

__all__ = ["ProductContext", "EnrichedBehaviourContext", "ContextEnricher", "context_enricher"]


@dataclass
class EnrichedBehaviourContext:
    primary_entity_id: int
    product: ProductContext
    zone_code: str
    zone_risk_multiplier: float
    shift_fatigue_multiplier: float = 1.0


class ContextEnricher:
    """Enriches detections with deterministic product/SKU and warehouse zone context.

    Resolution order for `sku_or_class` (see product_catalog.py for why there's
    no single "the" product lookup): an exact match in the caller-supplied SKU
    catalog first (real product master data, when a warehouse has it) — then
    a per-detected-object-class default profile — then a generic fallback.
    Every returned ProductContext carries `profile_source` so callers can tell
    a verified SKU match from a class-based guess.
    """

    DEFAULT_PRODUCT = GENERIC_FALLBACK_PROFILE

    ZONE_MULTIPLIERS: Dict[str, float] = {
        "LOADING_DOCK": 1.4,
        "WET_FLOOR": 2.0,
        "HIGH_RACK_AISLE": 1.6,
        "FORKLIFT_TRANSIT": 1.5,
        "BUFFER_STAGING": 1.0,
        "PACKING_STATION": 1.1,
    }

    def __init__(self, catalog: Optional[Dict[str, ProductContext]] = None):
        # Real SKU master data, if the caller has any (falls back to the
        # illustrative demo catalog so existing call sites that pass a
        # "SKU-..." string keep resolving as before).
        self.catalog = {**DEMO_SKU_CATALOG, **(catalog or {})}

    def get_product_context(self, sku_or_class: Optional[str] = None) -> ProductContext:
        if sku_or_class:
            if sku_or_class in self.catalog:
                profile = self.catalog[sku_or_class]
                return dataclasses.replace(profile, profile_source="CONFIGURED_SKU")
            if sku_or_class in CLASS_DEFAULT_PROFILES:
                return CLASS_DEFAULT_PROFILES[sku_or_class]
        return dataclasses.replace(self.DEFAULT_PRODUCT, profile_source="GENERIC_FALLBACK")

    def get_zone_multiplier(self, zone_code: Optional[str]) -> float:
        if not zone_code:
            return 1.0
        normalized = zone_code.upper().replace(" ", "_")
        for key, mult in self.ZONE_MULTIPLIERS.items():
            if key in normalized:
                return mult
        return 1.0

    def enrich(
        self,
        entity_id: int,
        sku_or_class: Optional[str] = None,
        zone_code: Optional[str] = None,
        shift_hours: float = 4.0,
    ) -> EnrichedBehaviourContext:
        prod = self.get_product_context(sku_or_class)
        z_mult = self.get_zone_multiplier(zone_code)
        shift_mult = 1.0 + (0.15 if shift_hours > 7.0 else 0.0)

        return EnrichedBehaviourContext(
            primary_entity_id=entity_id,
            product=prod,
            zone_code=zone_code or "DEFAULT_ZONE",
            zone_risk_multiplier=z_mult,
            shift_fatigue_multiplier=shift_mult,
        )


context_enricher = ContextEnricher()
