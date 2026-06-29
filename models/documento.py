from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field

class DocumentMetadata(Document):
    original_filename: str
    content_type: str
    extension: str
    size_bytes: int
    
    # Adicionado para cumprir o requisito do TP3 de registar a data/hora do upload
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Guardamos a referência direta ao Produto através do seu ID no formato do MongoDB
    produto_id: PydanticObjectId
    
    class Settings:
        name = "documents"