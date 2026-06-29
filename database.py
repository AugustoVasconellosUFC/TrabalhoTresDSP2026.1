import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

# Importe os seus modelos para o Beanie mapear
from models.produto import Produto
from models.document import DocumentMetadata

# Executa a função correta para carregar as variáveis do .env para a memória
load_dotenv()

async def init_db():
    # 1. Recupera a string de conexão do .env
    mongo_url = os.getenv("MONGO_URL")
    
    # 2. Cria o cliente assíncrono
    client = AsyncIOMotorClient(mongo_url)
    
    # 3. Define a base de dados (o motor extrai o nome automaticamente da URL)
    db = client.get_default_database()
    
    # 4. Inicializa o Beanie com a lista de modelos do projeto
    await init_beanie(
        database=db,
        document_models=[
            Produto,
            DocumentMetadata,
            # Adicione as outras entidades da tripla aqui quando as criarem
        ]
    )