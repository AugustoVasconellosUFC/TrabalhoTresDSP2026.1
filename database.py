import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
<<<<<<< HEAD
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
=======

# Importação dos modelos (entidades) que serão mapeados no MongoDB
# Importante: Todas essas classes precisam herdar de beanie.Document
from entidades.usuario import Usuario
from entidades.loja import Loja
from entidades.produto import Produto
from entidades.pedido import Pedido
from entidades.documento import Documento

async def init_db():
    # Busca a URL de conexão do arquivo .env.
    # Caso não encontre (ex: rodando fora do Docker sem carregar o .env ainda), usa um fallback.
    mongo_url = os.getenv("MONGO_URL", "mongodb://mongo:27017/trabalhotres")
    
    # 1. Instancia o cliente do Motor (driver assíncrono do MongoDB)
    client = AsyncIOMotorClient(mongo_url)
    
    # 2. Seleciona o banco de dados (o Motor extrai o nome do banco da URL,
    # mas você pode forçar um nome específico como abaixo)
    db = client.get_database("trabalhotres")
    
    # 3. Inicializa o Beanie com o banco de dados e a lista de TODOS os modelos de coleção.
    # O modelo Endereco NÃO entra aqui pois será um documento embutido (BaseModel) no Usuario.
    await init_beanie(
        database=db,
        document_models=[
            Usuario,
            Loja,
            Produto,
            Pedido,
            Documento
>>>>>>> d4c90c4aba60ee0987fffb5412a41a7f083a33db
        ]
    )