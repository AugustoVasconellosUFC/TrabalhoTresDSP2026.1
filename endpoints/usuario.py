from fastapi import APIRouter, HTTPException, status, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.beanie import paginate
from beanie import PydanticObjectId
from typing import Optional
import re

from entidades.usuario import Usuario

router = APIRouter()

@router.post("/", response_model=Usuario, status_code=status.HTTP_201_CREATED, summary="Criar um novo utilizador")
async def criar_usuario(usuario: Usuario):
    try:
        await usuario.insert()
        return usuario
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao inserir o utilizador: {str(e)}"
        )

@router.get("/", response_model=Page[Usuario], summary="Listar utilizadores com paginação")
async def listar_usuarios(nome: Optional[str] = Query(None, description="Busca por texto parcial e case-insensitive no nome")):
    try:
        if nome:
            # Requisito C: Busca por texto parcial e case-insensitive utilizando regex
            regex_filtro = re.compile(nome, re.IGNORECASE)
            return await paginate(Usuario.find(Usuario.nome == regex_filtro))
        
        # Requisito: Nunca carregar a tabela inteira, aplicando paginação padrão
        return await paginate(Usuario.find_all())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar utilizadores: {str(e)}"
        )

@router.get("/{id}", response_model=Usuario, summary="Obter dados de um utilizador pelo ID")
async def obter_usuario(id: PydanticObjectId):
    usuario = await Usuario.get(id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador não encontrado")
    return usuario

@router.put("/{id}", response_model=Usuario, summary="Atualizar um utilizador existente")
async def atualizar_usuario(id: PydanticObjectId, dados_atualizados: Usuario):
    usuario = await Usuario.get(id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador não encontrado")
    
    try:
        # Atualização dos campos do documento existente
        usuario.nome = dados_atualizados.nome
        usuario.email = dados_atualizados.email
        usuario.senha = dados_atualizados.senha
        usuario.endereco = dados_atualizados.endereco
        usuario.lojas_favoritas = dados_atualizados.lojas_favoritas
        usuario.documentos = dados_atualizados.documentos
        
        await usuario.save()
        return usuario
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao atualizar o utilizador: {str(e)}"
        )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover um utilizador")
async def eliminar_usuario(id: PydanticObjectId):
    usuario = await Usuario.get(id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador não encontrado")
    
    try:
        await usuario.delete()
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao eliminar o utilizador: {str(e)}"
        )