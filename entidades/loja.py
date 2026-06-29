from typing import List, Optional
from beanie import Document, Link
from pydantic import Field, EmailStr
from datetime import datetime, timezone

# Importando o modelo embutido (BaseModel) de endereço
from entidades.endereço import Endereco

# Importando as outras entidades para criar os relacionamentos (Links)
from entidades.loja import Loja
from entidades.documento import Documento

class Usuario(Document):
    nome: str = Field(..., max_length=150, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail válido e único do usuário")
    senha: str = Field(..., description="Hash da senha do usuário")
    
    # 1. Documento Embutido
    # O endereço será salvo diretamente dentro do JSON/BSON do usuário no MongoDB
    endereco: Optional[Endereco] = None
    
    # 2. Relacionamento Muitos-para-Muitos (N:M)
    # Exemplo: O usuário pode seguir/favoritar várias lojas
    lojas_favoritas: Optional[List[Link[Loja]]] = []
    
    # 3. Relacionamento Um-para-Muitos (1:N)
    # Atendendo ao requisito: "A aplicação deve permitir que pelo menos uma entidade tenha um ou mais documentos associados."
    documentos: Optional[List[Link[Documento]]] = []
    
    data_criacao: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "usuarios" # Define explicitamente o nome da coleção no MongoDB