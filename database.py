import os
from pymongo import AsyncMongoClient
from beanie import init_beanie

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
    
    # 1. Instancia o cliente assíncrono nativo do PyMongo (o Beanie 2.x não usa mais o Motor)
    client = AsyncMongoClient(mongo_url)

    # 2. Seleciona o banco de dados (pode extrair o nome da URL,
    # mas aqui forçamos um nome específico)
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
        ]
    )