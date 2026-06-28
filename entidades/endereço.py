from typing import List, Optional
from beanie import Document
from pydantic import BaseModel, Field

# Endereço agora é um documento embutido na entidade Usuario
class Endereco(BaseModel):
    rua: str
    cidade: str
    estado: str
    cep: str