from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import FastAPI, HTTPException, status 
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db, get_orders_collection
from .models import OrderCreate, OrderUpdate, OrderInDB


app = FastAPI(
    title="WMS Orders Microservice",
    version="1.0.0",
    description="Microservicio de pedidos para el WMS, usando FastAPI + MongoDB.",
)


# CORS básico (ajusta orígenes según tus frontends o pruebas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción restringe esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Se ejecuta cuando arranca el microservicio.
    Inicializamos la conexión a Mongo y creamos índices.
    """
    init_db()
    orders_collection = get_orders_collection()
    # Índices útiles para mantener el rendimiento (latencia < 0.5s)
    await orders_collection.create_index("external_id", unique=True)
    await orders_collection.create_index("status")
    await orders_collection.create_index("warehouse_id")


def _order_doc_to_model(doc) -> OrderInDB:
    return OrderInDB(
        id=str(doc["_id"]),
        external_id=doc["external_id"],
        warehouse_id=doc["warehouse_id"],
        status=doc["status"],
        picker_id=doc.get("picker_id"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@app.get("/health", tags=["health"])
async def health_check():
    """
    Endpoint de salud para que el API Gateway monitoree el estado del microservicio.
    """
    return {"status": "ok"}


@app.post("/orders", response_model=OrderInDB, status_code=status.HTTP_201_CREATED, tags=["orders"])
async def create_order(order: OrderCreate):
    """
    Crea un nuevo pedido.
    """
    orders_collection = get_orders_collection()

    now = datetime.utcnow()
    doc = {
        "external_id": order.external_id,
        "warehouse_id": order.warehouse_id,
        "status": order.status,
        "picker_id": order.picker_id,
        "created_at": now,
        "updated_at": now,
    }

    # Evitar pedidos duplicados por external_id
    existing = await orders_collection.find_one({"external_id": order.external_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un pedido con external_id={order.external_id}",
        )

    result = await orders_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _order_doc_to_model(doc)


@app.get("/orders", response_model=List[OrderInDB], tags=["orders"])
async def list_orders(status_filter: str | None = None, warehouse_id: str | None = None):
    """
    Lista pedidos con filtros opcionales (por estado y/o bodega).
    Esto se usa, por ejemplo, para asignar alistadores rápidamente.
    """
    orders_collection = get_orders_collection()

    query: dict = {}
    if status_filter:
        query["status"] = status_filter
    if warehouse_id:
        query["warehouse_id"] = warehouse_id

    cursor = orders_collection.find(query).sort("created_at", 1)
    results = []
    async for doc in cursor:
        results.append(_order_doc_to_model(doc))

    return results


@app.get("/orders/{order_id}", response_model=OrderInDB, tags=["orders"])
async def get_order(order_id: str):
    """
    Obtiene un pedido por su ID interno (Mongo _id).
    """
    orders_collection = get_orders_collection()

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de pedido inválido")

    doc = await orders_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

    return _order_doc_to_model(doc)


@app.put("/orders/{order_id}", response_model=OrderInDB, tags=["orders"])
async def update_order(order_id: str, update: OrderUpdate):
    """
    Actualiza el estado y/o el alistador de un pedido.
    Este endpoint es crítico para la métrica de latencia de asignación (< 0.5 s).
    """
    orders_collection = get_orders_collection()

    try:
        oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de pedido inválido")

    update_fields = {k: v for k, v in update.dict(exclude_unset=True).items()}
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay campos para actualizar")

    update_fields["updated_at"] = datetime.utcnow()

    result = await orders_collection.find_one_and_update(
        {"_id": oid},
        {"$set": update_fields},
        return_document=True,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

    return _order_doc_to_model(result)
