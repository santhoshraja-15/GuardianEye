"""
Product / Object-Class Risk Profile Catalog

    Detected Object -> Object Class -> Product / SKU -> Product Risk Profile
    -> Behaviour Context -> Risk Calculation

The perception layer only ever gives us an object *class* (one of
YOLODetector.CLASS_NAMES — "person", "carton", "pallet", ...), never a
real SKU: there is no barcode/label recognition in this pipeline. Rather
than pretend otherwise by stamping every event with the same demo carton
SKU regardless of what was actually detected, this module is honest about
that boundary:

  - CLASS_DEFAULT_PROFILES: a configured risk profile per detected object
    *class* — used whenever no real SKU is known, which today is always.
    These are clearly-labeled placeholders standing in for "we know it's
    a carton, we don't know which one" rather than fabricated product
    identity.
  - DEMO_SKU_CATALOG: example real-SKU profiles, kept for warehouses that
    *do* have SKU data (e.g. from a WMS integration) to plug in via
    ContextEnricher(catalog=...). Not used unless a caller supplies a real
    SKU code.

`profile_source` on every resolved profile tells the caller (and, if
surfaced, the UI/assistant) which of these actually happened, so nothing
downstream can present a class-default guess as if it were verified
product data.
"""
from dataclasses import dataclass, field
from typing import Dict


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
    # False for people and powered equipment — a risk profile still applies
    # (safety/asset-damage), but "product fragility/damage" framing doesn't.
    is_product: bool = True
    # "CONFIGURED_SKU" | "CLASS_DEFAULT" | "GENERIC_FALLBACK" — set by
    # ContextEnricher.get_product_context, not by the profile itself.
    profile_source: str = field(default="CLASS_DEFAULT")


# Per-detected-class defaults. Every class YOLODetector can emit has an
# entry so lookups never silently fall through to a mismatched profile.
CLASS_DEFAULT_PROFILES: Dict[str, ProductContext] = {
    "carton": ProductContext(
        sku="CLASS-CARTON",
        product_name="Generic Carton / Parcel",
        category="General Goods",
        fragility_rating=3,
        unit_value_usd=120.0,
        max_safe_drop_height_px=25.0,
        max_stack_height_units=4,
        weight_kg=8.0,
    ),
    "pallet": ProductContext(
        sku="CLASS-PALLET",
        product_name="Loaded Pallet",
        category="Palletized Goods",
        fragility_rating=2,
        unit_value_usd=600.0,
        max_safe_drop_height_px=15.0,
        max_stack_height_units=1,
        requires_upright_orientation=True,
        weight_kg=250.0,
    ),
    "trolley": ProductContext(
        sku="CLASS-TROLLEY",
        product_name="Handling Trolley",
        category="Warehouse Equipment",
        fragility_rating=1,
        unit_value_usd=300.0,
        max_safe_drop_height_px=50.0,
        weight_kg=40.0,
        is_product=False,
    ),
    "forklift": ProductContext(
        sku="CLASS-FORKLIFT",
        product_name="Forklift / Industrial Vehicle",
        category="Powered Equipment",
        fragility_rating=1,
        unit_value_usd=25000.0,
        max_safe_drop_height_px=999.0,
        weight_kg=2500.0,
        is_product=False,
    ),
    "equipment": ProductContext(
        sku="CLASS-EQUIPMENT",
        product_name="Handling Equipment",
        category="Warehouse Equipment",
        fragility_rating=1,
        unit_value_usd=800.0,
        max_safe_drop_height_px=40.0,
        weight_kg=30.0,
        is_product=False,
    ),
    "stack": ProductContext(
        sku="CLASS-STACK",
        product_name="Stacked Carton Group",
        category="General Goods",
        fragility_rating=3,
        unit_value_usd=400.0,
        max_safe_drop_height_px=20.0,
        max_stack_height_units=5,
        weight_kg=32.0,
    ),
    "person": ProductContext(
        sku="CLASS-PERSON",
        product_name="Operator",
        category="Human Subject",
        fragility_rating=0,
        unit_value_usd=0.0,
        is_product=False,
    ),
    "loading_bay": ProductContext(
        sku="CLASS-LOADING-BAY",
        product_name="Loading Bay Fixture",
        category="Facility",
        fragility_rating=0,
        unit_value_usd=0.0,
        is_product=False,
    ),
    "floor": ProductContext(
        sku="CLASS-FLOOR",
        product_name="Floor Surface",
        category="Facility",
        fragility_rating=0,
        unit_value_usd=0.0,
        is_product=False,
    ),
}

# Real-SKU examples for warehouses with actual product master data. Kept
# separate from the class defaults so it's obvious these are illustrative
# configured entries, not something the vision pipeline detected.
DEMO_SKU_CATALOG: Dict[str, ProductContext] = {
    "SKU-CARTON-STD": ProductContext(
        sku="SKU-CARTON-STD",
        product_name="Standard Packaging Carton",
        category="General Goods",
        fragility_rating=3,
        unit_value_usd=120.0,
        max_safe_drop_height_px=25.0,
        profile_source="CONFIGURED_SKU",
    ),
    "SKU-OPTICS": ProductContext(
        sku="SKU-OPTICS",
        product_name="Precision Industrial Optics",
        category="Electronics & Optics",
        fragility_rating=5,
        unit_value_usd=850.0,
        max_safe_drop_height_px=15.0,
        profile_source="CONFIGURED_SKU",
    ),
    "SKU-HEAVY-FURNITURE": ProductContext(
        sku="SKU-HEAVY-FURNITURE",
        product_name="Heavy Cabinet / Furniture",
        category="Heavy Goods",
        fragility_rating=4,
        unit_value_usd=450.0,
        max_safe_drop_height_px=10.0,
        profile_source="CONFIGURED_SKU",
    ),
}

GENERIC_FALLBACK_PROFILE = ProductContext(
    sku="GENERIC-UNKNOWN",
    product_name="Unidentified Object",
    category="General Goods",
    fragility_rating=2,
    unit_value_usd=50.0,
    max_safe_drop_height_px=40.0,
    max_stack_height_units=5,
    profile_source="GENERIC_FALLBACK",
)
