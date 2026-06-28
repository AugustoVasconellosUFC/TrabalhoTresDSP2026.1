import os
import asyncio
from minio import Minio
from fastapi import HTTPException, status

# Inicialização do cliente MinIO com as credenciais do .env
minio_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
    secure=False # Falso porque não estamos a usar HTTPS no ambiente local
)

BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "documentos")

def init_minio():
    """Garante que o bucket existe ao iniciar a aplicação."""
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' criado no MinIO.")

async def upload_arquivo(nome_arquivo: str, arquivo_stream, tamanho: int, content_type: str):
    """Envia um ficheiro para o MinIO."""
    try:
        await asyncio.to_thread(
            minio_client.put_object,
            bucket_name=BUCKET_NAME,
            object_name=nome_arquivo,
            data=arquivo_stream,
            length=tamanho,
            content_type=content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar arquivo físico no MinIO: {str(e)}"
        )

async def download_arquivo(nome_arquivo: str):
    """Recupera um ficheiro do MinIO."""
    try:
        # get_object retorna um stream HTTP que precisa de ser lido
        resposta = await asyncio.to_thread(
            minio_client.get_object, BUCKET_NAME, nome_arquivo
        )
        return resposta
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao recuperar arquivo do MinIO: {str(e)}"
        )

async def deletar_arquivo(nome_arquivo: str):
    """Remove um ficheiro fisicamente do MinIO."""
    try:
        await asyncio.to_thread(
            minio_client.remove_object, BUCKET_NAME, nome_arquivo
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover arquivo físico no MinIO: {str(e)}"
        )