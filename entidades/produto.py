from beanie import Document, Link
from pydantic import BaseModel
from typing import Optional
# Supondo que Loja já esteja definida em outro arquivo de models
from models.loja import Loja 

class Produto(Document):
    nome: str
    descricao: str
    preco: float
    loja: Link[Loja]  # Referência assíncrona para a coleção de Lojas

    class Settings:
        name = "produtos"  # Nome da coleção no MongoDB