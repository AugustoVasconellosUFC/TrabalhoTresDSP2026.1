import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from beanie import PydanticObjectId

# Importando os modelos refatorados para o MongoDB/Beanie
from entidades.endereco import Endereco
from entidades.usuario import Usuario

router = APIRouter(prefix="/enderecos", tags=["Endereços"])


# Modificado: O usuario_id agora espera o formato ID do MongoDB (string/ObjectId)
class EnderecoCreate(BaseModel):
    rua: str
    cidade: str
    estado: str
    cep: str
    usuario_id: PydanticObjectId


class EnderecoUpdate(BaseModel):
    rua: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None


@router.get("/", summary="Listar endereços (paginado)")
async def listar_enderecos(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
):
    """Lista todos os endereços espalhados entre os usuários usando agregação do MongoDB."""
    skip = (page - 1) * size

    # Pipeline de agregação para extrair e paginar os subdocumentos de endereço
    pipeline_dados = [
        {"$unwind": "$enderecos"},  # Transforma o array de endereços em múltiplos documentos
        {"$skip": skip},
        {"$limit": size},
        {
            "$project": {
                "rua": "$enderecos.rua",
                "cidade": "$enderecos.cidade",
                "estado": "$enderecos.estado",
                "cep": "$enderecos.cep",
                "usuario_id": "$_id",  # Mantém a referência de quem é o dono
            }
        },
    ]

    pipeline_total = [{"$unwind": "$enderecos"}, {"$count": "total"}]

    # Executa as agregações na coleção de usuários
    resultado_dados = await Usuario.aggregate(pipeline_dados).to_list()
    resultado_total = await Usuario.aggregate(pipeline_total).to_list()

    total = resultado_total[0]["total"] if resultado_total else 0

    return {
        "items": resultado_dados,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total > 0 else 0,
    }


@router.get(
    "/usuario/{usuario_id}",
    response_model=list[Endereco],
    summary="Listar endereços de um usuário",
)
async def listar_enderecos_por_usuario(usuario_id: PydanticObjectId):
    """Retorna a lista de endereços embutidos diretamente no documento do usuário."""
    usuario = await Usuario.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return usuario.enderecos


@router.post("/", response_model=Endereco, status_code=201, summary="Criar endereço")
async def criar_endereco(dados: EnderecoCreate):
    """Adiciona um novo endereço dentro do array do usuário correspondente."""
    usuario = await Usuario.get(dados.usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Instancia o subdocumento (sem o usuario_id, que já é o dono do documento pai)
    novo_endereco = Endereco(
        rua=dados.rua, cidade=dados.cidade, estado=dados.estado, cep=dados.cep
    )

    # Adiciona o endereço na lista local e salva no MongoDB
    usuario.enderecos.append(novo_endereco)
    await usuario.save()

    return novo_endereco


@router.put(
    "/usuario/{usuario_id}/index/{endereco_index}",
    response_model=Endereco,
    summary="Atualizar endereço por índice",
)
async def atualizar_endereco(
    usuario_id: PydanticObjectId, endereco_index: int, dados: EnderecoUpdate
):
    """Atualiza um endereço específico de um usuário baseado na sua posição (índice) no array."""
    usuario = await Usuario.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verifica se o índice fornecido é válido no array do usuário
    if endereco_index < 0 or endereco_index >= len(usuario.enderecos):
        raise HTTPException(status_code=404, detail="Endereço não encontrado")

    endereco_atual = usuario.enderecos[endereco_index]

    # Atualiza apenas os campos enviados no body (exclude_none=True)
    dados_atualizados = dados.model_dump(exclude_none=True)
    for campo, valor in dados_atualizados.items():
        setattr(endereco_atual, campo, valor)

    # Substitui no array e salva o documento do usuário atualizado
    usuario.enderecos[endereco_index] = endereco_atual
    await usuario.save()

    return endereco_atual


@router.delete(
    "/usuario/{usuario_id}/index/{endereco_index}",
    status_code=204,
    summary="Deletar endereço por índice",
)
async def deletar_endereco(usuario_id: PydanticObjectId, endereco_index: int):
    """Remove um endereço do array de um usuário baseado na sua posição (índice)."""
    usuario = await Usuario.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if endereco_index < 0 or endereco_index >= len(usuario.enderecos):
        raise HTTPException(status_code=404, detail="Endereço não encontrado")

    # Remove o endereço da lista por índice e atualiza o MongoDB
    usuario.enderecos.pop(endereco_index)
    await usuario.save()
