from typing import List
from datetime import datetime, timezone
from beanie import Document, Link
from pydantic import BaseModel, Field
from entidades.usuario import Usuario 
from entidades.produto import Produto

# Documento Principal do Pedido no Beanie
class Pedido(Document):
    # O Beanie gera o id (ObjectId) automaticamente
    data_criacao: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pendente"
    
    # Referência direta para o documento do Usuário (Substitui o usuario_id)
    usuario: Link[Usuario]
    
    # Lista de produtos incorporados diretamente no pedido (Substitui a tabela intermediária N:M)
    produtos: List[Link[Produto]]

    class Settings:
        name = "pedidos"  # Nome da coleção no MongoDB
