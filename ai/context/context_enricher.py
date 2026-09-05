"""
Context Enrichment Engine for GuardianEye
Associates product fragility, SKU metadata, zone risk profiles, and operational parameters with detected behaviour events.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProductContext:
    sku: str
    product_name: str
    category: str
    fragility_rating: int  # 1 (rugged) to 5 (extremely delicate: electronics/glass)
    unit_value_usd: float
    max_safe_drop_height_px: float = 30.0
    max_stack_height_units: int = 4
    requires_upright_orientation: bool = True
    weight_kg: float = 5.0


@dataclass
class EnrichedBehaviourContext:
    primary_entity_id: int
    product: ProductContext
    zone_code: str
    zone_risk_multiplier: float
    shift_fatigue_multiplier: float = 1.0


class ContextEnricher:
    """Enriches detections with deterministic SKU and warehouse zone context."""

    DEFAULT_PRODUCT = ProductContext(
        sku="SKU-GENERIC-BOX",
        product_name="Standard Shipping Carton",
        category="General Goods",
        fragility_rating=2,
        unit_value_usd=50.0,
        max_safe_drop_height_px=40.0,
        max_stack_height_units=5,
    )

    ZONE_MULTIPLIERS: Dict[str, float] = {
        "LOADING_DOCK": 1.4,
        "WET_FLOOR": 2.0,
        "HIGH_RACK_AISLE": 1.6,
        "FORKLIFT_TRANSIT": 1.5,
        "BUFFER_STAGING": 1.0,
        "PACKING_STATION": 1.1,
    }

    def __init__(self, catalog: Optional[Dict[str, ProductContext]] = None):
        self.catalog = catalog or {}

    def get_product_context(self, sku_or_class: Optional[str] = None) -> ProductContext:
        if sku_or_class and sku_or_class in self.catalog:
            return self.catalog[sku_or_class]
        return self.DEFAULT_PRODUCT

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
