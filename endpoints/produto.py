import io
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel
from beanie import PydanticObjectId
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import paginate

from entidades.produto import Produto
from entidades.loja import Loja
from entidades.documento import Documento
from servicos.minio_service import minio_client, BUCKET_NAME

router = APIRouter(prefix="/produtos", tags=["Produtos"])


# ==========================================
# Esquemas Pydantic (Entrada de Dados)
# ==========================================
class ProdutoCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    estoque: int = 0
    loja_id: str  # Em NoSQL, recebemos a string e convertemos para PydanticObjectId

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    estoque: Optional[int] = None


# ==========================================
# Listagem e Consultas (Produtos)
# ==========================================

@router.get("/", response_model=Page[Produto], summary="Listar produtos (paginado)")
async def listar_produtos():
    """
    Lógica (Passo a Passo):
    1. Realiza uma query para encontrar todos os produtos.
    2. Utiliza fetch_links=True para trazer os dados da Loja referenciada.
    3. Aplica a paginação exigida pelo trabalho e retorna.
    """
    return await paginate(Produto.find_all(fetch_links=True))


@router.get("/stats/total", summary="Quantidade total de produtos cadastrados")
async def total_produtos():
    """
    Lógica (Passo a Passo):
    1. Executa a função count() nativa do MongoDB.
    2. Retorna o total num dicionário.
    """
    total = await Produto.count()
    return {"total_produtos": total}


@router.get("/buscar", response_model=List[Produto], summary="Buscar produtos por nome")
async def buscar_produtos(nome: str = Query(..., description="Texto a buscar no nome do produto")):
    """
    Lógica (Passo a Passo):
    1. Constrói uma expressão regular para buscar o termo em qualquer parte do nome.
    2. Aplica a opção 'i' para tornar a busca insensível a maiúsculas/minúsculas.
    3. Retorna a lista resolvida.
    """
    return await Produto.find(
        {"nome": {"$regex": nome, "$options": "i"}},
        fetch_links=True
    ).to_list()


@router.get("/preco", response_model=List[Produto], summary="Filtrar produtos por preço mínimo")
async def produtos_acima_do_preco(min: float = Query(..., description="Preço mínimo (inclusive)")):
    """
    Lógica (Passo a Passo):
    1. Utiliza o operador de comparação >= diretamente no atributo preço.
    2. Ordena os resultados pelo preço em ordem decrescente (sinal de menos antes do atributo).
    """
    return await Produto.find(Produto.preco >= min, fetch_links=True).sort(-Produto.preco).to_list()


@router.get("/{produto_id}", response_model=Produto, summary="Buscar produto por ID")
async def buscar_produto(produto_id: str):
    """
    Lógica (Passo a Passo):
    1. Valida o formato do ID para evitar crashs (resiliência).
    2. Busca o documento; se não existir, lança erro 404.
    """
    if not PydanticObjectId.is_valid(produto_id):
        raise HTTPException(status_code=400, detail="ID de produto inválido.")

    produto = await Produto.get(PydanticObjectId(produto_id), fetch_links=True)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


# ==========================================
# Operações CRUD (Produtos)
# ==========================================

@router.post("/", response_model=Produto, status_code=status.HTTP_201_CREATED, summary="Criar produto")
async def criar_produto(dados: ProdutoCreate):
    """
    Lógica (Passo a Passo):
    1. Verifica a validade do ID da Loja.
    2. Confirma se a Loja existe na base de dados.
    3. Injeta a referência da loja e salva o novo produto.
    """
    if not PydanticObjectId.is_valid(dados.loja_id):
        raise HTTPException(status_code=400, detail="ID da loja inválido.")

    loja = await Loja.get(PydanticObjectId(dados.loja_id))
    if not loja:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")

    produto = Produto(
        nome=dados.nome,
        descricao=dados.descricao,
        preco=dados.preco,
        estoque=dados.estoque,
        loja=loja
    )
    await produto.insert()
    return produto


@router.put("/{produto_id}", response_model=Produto, summary="Atualizar produto")
async def atualizar_produto(produto_id: str, dados: ProdutoUpdate):
    """
    Lógica (Passo a Passo):
    1. Recupera o produto existente utilizando a função de busca.
    2. Itera sobre os campos enviados no payload; se não forem nulos, atualiza o atributo.
    3. Salva as alterações na base de dados.
    """
    produto = await buscar_produto(produto_id)

    dados_dict = dados.model_dump(exclude_unset=True)
    for campo, valor in dados_dict.items():
        setattr(produto, campo, valor)

    await produto.save()
    return produto


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deletar produto")
async def deletar_produto(produto_id: str):
    """
    Lógica (Passo a Passo):
    1. Localiza o produto.
    2. Remove-o do MongoDB.
    """
    produto = await buscar_produto(produto_id)
    await produto.delete()


# ==========================================
# Gestão de Ficheiros (Upload para Produto)
# ==========================================

@router.post("/{produto_id}/documents", response_model=Documento, status_code=status.HTTP_201_CREATED)
async def upload_documento_produto(produto_id: str, file: UploadFile = File(...)):
    """
    Lógica (Passo a Passo):
    1. Confirma a existência do produto.
    2. Extrai as propriedades do ficheiro binário.
    3. Grava o registo na coleção de metadados para obter um ID.
    4. Grava o binário no MinIO utilizando o ID como nome.
    """
    produto = await buscar_produto(produto_id)

    conteudo = await file.read()
    extensao = Path(file.filename).suffix.lower() if file.filename else ""

    # 3. Metadados no Mongo
    doc = Documento(
        original_filename=file.filename or "sem_nome",
        content_type=file.content_type or "application/octet-stream",
        extension=extensao,
        size_bytes=len(conteudo),
        produto_id=produto.id
    )
    await doc.insert()

    # 4. Binário no MinIO
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)

    nome_fisico = f"{str(doc.id)}{extensao}"

    try:
        minio_client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=nome_fisico,
            data=io.BytesIO(conteudo),
            length=len(conteudo),
            content_type=doc.content_type
        )
    except Exception:
        await doc.delete()
        raise HTTPException(status_code=500, detail="Erro ao guardar o ficheiro físico no servidor.")

    return doc


@router.get("/{produto_id}/documents", response_model=List[Documento])
async def listar_documentos_produto(produto_id: str):
    """
    Lógica (Passo a Passo):
    1. Valida o formato do ID.
    2. Busca todos os documentos que possuem o ID deste produto associado.
    """
    if not PydanticObjectId.is_valid(produto_id):
        raise HTTPException(status_code=400, detail="ID de produto inválido.")

    return await Documento.find(Documento.produto_id == PydanticObjectId(produto_id)).to_list()