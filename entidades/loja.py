from typing import List, Optional
from datetime import datetime, timezone
from beanie import Document, PydanticObjectId
from pydantic import Field


class Loja(Document):
    nome_fantasia: str = Field(..., max_length=150, description="Nome fantasia da loja")
    razao_social: str = Field(..., max_length=150, description="Razão social da loja")
    cnpj: str = Field(..., description="CNPJ da loja")
    telefone: Optional[str] = Field(None, description="Telefone de contato")
    ativa: bool = Field(default=True, description="Indica se a loja está ativa")

    # Referência aos produtos da loja pelos seus IDs no MongoDB (relação 1:N).
    # Guardamos apenas os IDs para evitar import circular com a entidade Produto.
    produtos: Optional[List[PydanticObjectId]] = []

    data_criacao: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "lojas"  # Nome da coleção no MongoDB