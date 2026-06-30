from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field


class Documento(Document):
    original_filename: str
    content_type: str
    extension: str
    size_bytes: int

    # Registra a data/hora do upload (requisito do TP3)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Referência direta ao Produto através do seu ID no MongoDB (relação 1:N)
    produto_id: PydanticObjectId

    class Settings:
        name = "documentos"  # Nome da coleção no MongoDB