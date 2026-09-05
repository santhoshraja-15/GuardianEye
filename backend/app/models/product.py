"""
Product, Category, and Equipment ORM Entities
"""
from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    fragility_index: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 (durable) to 1.0 (extremely fragile)
    max_drop_height_cm: Mapped[float] = mapped_column(Float, default=30.0)
    max_stack_weight_kg: Mapped[float] = mapped_column(Float, default=100.0)
    requires_equipment: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("product_categories.id"), nullable=True, index=True
    )
    weight_kg: Mapped[float] = mapped_column(Float, default=5.0)
    dimensions_cm: Mapped[str] = mapped_column(String(50), default="30x30x30")  # LxWxH
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_orientation: Mapped[str] = mapped_column(String(20), default="ANY")  # VERTICAL_ONLY, HORIZONTAL_ONLY, ANY
    max_stack_layers: Mapped[int] = mapped_column(Integer, default=5)

    category: Mapped[Optional[ProductCategory]] = relationship("ProductCategory", back_populates="products")


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    equipment_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # FORKLIFT, TROLLEY, PALLET_JACK, CONVEYOR
    max_load_capacity_kg: Mapped[float] = mapped_column(Float, default=1500.0)
    max_safe_speed_kmh: Mapped[float] = mapped_column(Float, default=10.0)
    status: Mapped[str] = mapped_column(String(20), default="OPERATIONAL")  # OPERATIONAL, MAINTENANCE, RETIRED
