from typing import List
from datetime import datetime, timezone
from beanie import Document, Link
from pydantic import BaseModel, Field

from entidades.usuario import Usuario


# Snapshot embutido de um produto no momento da compra.
# Guarda nome e preço para preservar o histórico, mesmo que o produto mude depois.
class ItemPedido(BaseModel):
    produto_id: str
    nome: str
    preco_unitario: float
    quantidade: int = 1


# Documento Principal do Pedido no Beanie
class Pedido(Document):
    # O Beanie gera o id (ObjectId) automaticamente
    data_criacao: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pendente"

    # Referência direta ao documento do Usuário (Link do Beanie)
    usuario: Link[Usuario]

    # Lista de itens incorporados diretamente no pedido (snapshot histórico)
    produtos: List[ItemPedido] = []

    class Settings:
        name = "pedidos"  # Nome da coleção no MongoDB
