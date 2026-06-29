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