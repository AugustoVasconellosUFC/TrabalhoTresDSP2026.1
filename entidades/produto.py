from typing import Optional
from beanie import Document, Link

# Loja vem da pasta de entidades (não de "models")
from entidades.loja import Loja


class Produto(Document):
    nome: str
    descricao: str
    preco: float
    estoque: int = 0
    loja: Link[Loja]  # Referência assíncrona para a coleção de Lojas

    class Settings:
        name = "produtos"  # Nome da coleção no MongoDB