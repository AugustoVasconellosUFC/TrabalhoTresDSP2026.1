from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from database import init_db
from endpoints.usuario import router as usuario_router
from endpoints.loja import router as loja_router
from endpoints.produto import router as produto_router
from endpoints.pedido import router as pedido_router
from endpoints.documento import router as documento_router  # Rotas de metadados/download de documentos
from servicos.minio_service import init_minio

# O gerenciador de ciclo de vida (lifespan) substitui os antigos eventos startup/shutdown.
# Tudo o que for executado antes do 'yield' acontece quando a API está subindo.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa a conexão assíncrona com o MongoDB e registra os modelos do Beanie
    await init_db()
    print("Conexão com o MongoDB (Beanie ODM) inicializada com sucesso!")

    # Executa a verificação e criação do bucket do MinIO
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
app.include_router(produto_router, tags=["Produtos"])  # já possui prefix="/produtos"
app.include_router(pedido_router, tags=["Pedidos"])  # já possui prefix="/pedidos"
app.include_router(documento_router, tags=["Documentos"])  # já possui prefix="/documents"