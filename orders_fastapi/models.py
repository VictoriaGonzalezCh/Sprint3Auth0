from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderBase(BaseModel):
    external_id: str = Field(..., description="ID del pedido en el WMS/ERP/tienda")
    warehouse_id: str = Field(..., description="ID de la bodega donde se va a alistar")
    status: str = Field(default="CREATED", description="Estado del pedido (CREATED, ASSIGNED, PICKED, SHIPPED)")
    picker_id: Optional[str] = Field(default=None, description="ID del alistador asignado")


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    picker_id: Optional[str] = None


class OrderInDB(OrderBase):
    id: str = Field(..., description="ID interno del documento en MongoDB")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
