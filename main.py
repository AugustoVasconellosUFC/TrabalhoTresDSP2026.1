<<<<<<< HEAD
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executa a configuração do MongoDB na inicialização
    await init_db()
    yield
    # Código aqui executa quando a API desliga (se necessário)

app = FastAPI(lifespan=lifespan)
=======
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from database import init_db
from endpoints.usuario import router as usuario_router
from endpoints.loja import router as loja_router
from endpoints.documento import router as documento_router # Adicionado: Importação das rotas de documentos
from servicos.minio_service import init_minio

# O gerenciador de ciclo de vida (lifespan) substitui os antigos eventos startup/shutdown.
# Tudo o que for executado antes do 'yield' acontece quando a API está subindo.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa a conexão assíncrona com o MongoDB e registra os modelos do Beanie
    await init_db()
    print("Conexão com o MongoDB (Beanie ODM) inicializada com sucesso!")
    
    # Adicionado: Executa a verificação e criação do bucket do MinIO
    init_minio()
    print("Infraestrutura do MinIO pronta para uso!")
    
    yield
    # Código aqui dentro após o yield seria executado no encerramento da API (se necessário)

# Criação da instância do FastAPI configurando títulos e a documentação automática
app = FastAPI(
    title="API Web com FastAPI, MongoDB e MinIO",
    description="Trabalho Prático de Persistência de Dados - CRUD Assíncrono com Beanie ODM.",
    version="1.0.0",
    lifespan=lifespan
)

# Ativa globalmente o suporte a paginação exigido pelo escopo do projeto
add_pagination(app)

# Rota básica inicial para verificar se o servidor está online
@app.get("/", tags=["Root"])
async def root():
    return {
        "status": "online",
        "message": "API rodando com sucesso. Acesse /docs para visualizar a documentação Swagger/OpenAPI."
    }

# Registro das rotas
app.include_router(usuario_router, prefix="/usuarios", tags=["Usuários"])
app.include_router(loja_router, prefix="/lojas", tags=["Lojas"])
app.include_router(documento_router, tags=["Documentos"])
>>>>>>> d4c90c4aba60ee0987fffb5412a41a7f083a33db
