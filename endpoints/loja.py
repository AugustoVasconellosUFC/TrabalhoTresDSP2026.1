from fastapi import APIRouter, HTTPException, status, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import paginate
from beanie import PydanticObjectId
from typing import Optional
import re

from entidades.loja import Loja

router = APIRouter()

@router.post("/", response_model=Loja, status_code=status.HTTP_201_CREATED, summary="Criar uma nova loja")
async def criar_loja(loja: Loja):
    try:
        await loja.insert()
        return loja
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar a loja: {str(e)}"
        )

@router.get("/", response_model=Page[Loja], summary="Listar lojas com paginação")
async def listar_lojas(nome_fantasia: Optional[str] = Query(None, description="Busca por texto parcial no nome fantasia")):
    try:
        if nome_fantasia:
            regex_filtro = re.compile(nome_fantasia, re.IGNORECASE)
            return await paginate(Loja.find(Loja.nome_fantasia == regex_filtro))
        
        return await paginate(Loja.find_all())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar lojas: {str(e)}"
        )

@router.get("/{id}", response_model=Loja, summary="Obter dados de uma loja pelo ID")
async def obter_loja(id: PydanticObjectId):
    loja = await Loja.get(id)
    if not loja:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja não encontrada")
    return loja

@router.put("/{id}", response_model=Loja, summary="Atualizar uma loja existente")
async def atualizar_loja(id: PydanticObjectId, dados_atualizados: Loja):
    loja = await Loja.get(id)
    if not loja:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja não encontrada")
    
    try:
        loja.nome_fantasia = dados_atualizados.nome_fantasia
        loja.razao_social = dados_atualizados.razao_social
        loja.cnpj = dados_atualizados.cnpj
        loja.telefone = dados_atualizados.telefone
        loja.ativa = dados_atualizados.ativa
        loja.produtos = dados_atualizados.produtos
        
        await loja.save()
        return loja
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao atualizar a loja: {str(e)}"
        )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover uma loja")
async def eliminar_loja(id: PydanticObjectId):
    loja = await Loja.get(id)
    if not loja:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja não encontrada")
    
    try:
        await loja.delete()
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao eliminar a loja: {str(e)}"
        )