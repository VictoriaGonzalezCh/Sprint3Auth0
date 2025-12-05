import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "wms_orders")

client: AsyncIOMotorClient | None = None
db = None
orders_collection = None


def init_db():
    """
    Inicializa la conexión global a MongoDB.
    Llamar durante el startup de FastAPI.
    """
    global client, db, orders_collection
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        orders_collection = db["orders"]


def get_orders_collection():
    """
    Devuelve la colección de pedidos. Asegúrate de haber llamado init_db() antes.
    """
    if orders_collection is None:
        raise RuntimeError("La base de datos no ha sido inicializada. Llama init_db() en el startup.")
    return orders_collection
