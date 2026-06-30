import io
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId

from entidades.documento import Documento
from servicos.minio_service import minio_client, BUCKET_NAME

router = APIRouter(prefix="/documents", tags=["Documentos"])


@router.get("/{document_id}", response_model=Documento)
async def obter_metadados_documento(document_id: str):
    """
    GET /documents/{document_id}:
    Procura o documento pelo ID no MongoDB e devolve os metadados.
    """
    if not PydanticObjectId.is_valid(document_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    doc = await Documento.get(PydanticObjectId(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return doc


@router.get("/{document_id}/download")
async def download_documento(document_id: str):
    """
    GET /documents/{document_id}/download:
    1. Recupera os metadados para descobrir a extensão e o content type.
    2. Pede o objeto físico ao MinIO e devolve-o num StreamingResponse.
    """
    doc = await obter_metadados_documento(document_id)  # Reutiliza a função acima
    nome_fisico = f"{str(doc.id)}{doc.extension}"

    try:
        resposta_minio = minio_client.get_object(BUCKET_NAME, nome_fisico)
        return StreamingResponse(
            resposta_minio,
            media_type=doc.content_type,
            headers={"Content-Disposition": f"attachment; filename={doc.original_filename}"}
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Ficheiro físico não encontrado no MinIO")


@router.put("/{document_id}", response_model=Documento)
async def substituir_documento(document_id: str, file: UploadFile = File(...)):
    """
    PUT /documents/{document_id}:
    1. Localiza os metadados antigos.
    2. Remove o ficheiro físico antigo do MinIO.
    3. Faz o upload do novo ficheiro para o MinIO.
    4. Atualiza os metadados no MongoDB (tamanho, tipo, nova extensão) e guarda.
    """
    doc = await obter_metadados_documento(document_id)
    nome_fisico_antigo = f"{str(doc.id)}{doc.extension}"

    # 1. Remover o antigo do MinIO (ignora erro se já não existir)
    try:
        minio_client.remove_object(BUCKET_NAME, nome_fisico_antigo)
    except Exception:
        pass

    # 2. Ler novo ficheiro
    conteudo = await file.read()
    nova_extensao = Path(file.filename).suffix.lower() if file.filename else ""
    novo_nome_fisico = f"{str(doc.id)}{nova_extensao}"

    # 3. Enviar o novo ficheiro para o MinIO
    try:
        minio_client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=novo_nome_fisico,
            data=io.BytesIO(conteudo),
            length=len(conteudo),
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Falha ao gravar o novo ficheiro no MinIO")

    # 4. Atualizar os atributos no MongoDB
    doc.original_filename = file.filename or "sem_nome"
    doc.content_type = file.content_type or "application/octet-stream"
    doc.extension = nova_extensao
    doc.size_bytes = len(conteudo)

    await doc.save()
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_documento(document_id: str):
    """
    DELETE /documents/{document_id}:
    1. Localiza o documento no MongoDB.
    2. Apaga o ficheiro físico no MinIO.
    3. Apaga os metadados da base de dados.
    """
    doc = await obter_metadados_documento(document_id)
    nome_fisico = f"{str(doc.id)}{doc.extension}"

    # Remover do MinIO
    try:
        minio_client.remove_object(BUCKET_NAME, nome_fisico)
    except Exception:
        pass  # Prossegue para garantir a limpeza na base de dados

    # Remover do MongoDB
    await doc.delete()