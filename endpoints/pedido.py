import math
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from beanie import PydanticObjectId, Link

# Importando os modelos refatorados para o MongoDB/Beanie
from entidades.pedido import Pedido
from entidades.usuario import Usuario
from entidades.produto import Produto

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


class ItemPedidoCreate(BaseModel):
    produto_id: PydanticObjectId
    quantidade: int = 1


class PedidoCreate(BaseModel):
    usuario_id: PydanticObjectId
    status: str = "pendente"
    # Recebe uma lista de itens estruturados (ID e Quantidade)
    produtos: List[ItemPedidoCreate] = []


class PedidoUpdate(BaseModel):
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Listagens e consultas
# ---------------------------------------------------------------------------

@router.get("/", summary="Listar pedidos (paginado)")
async def listar_pedidos(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
):
    """Lista todos os pedidos com paginação calculando totais de forma embutida."""
    skip = (page - 1) * size
    total = await Pedido.count()
    
    # Busca os pedidos ordenados por data de criação decrescente
    pedidos = await Pedido.find_all().sort("-data_criacao").skip(skip).limit(size).to_list()
    
    # Como os produtos estão embutidos, calculamos os valores em memória rapidamente via Python/Pydantic
    items_formatados = []
    for p in pedidos:
        # Puxa o ID limpo do objeto Link do Beanie (sem carregar o usuário inteiro)
        usuario_id = p.usuario.ref.id
        
        valor_total = sum(item.preco_unitario * item.quantidade for item in p.produtos)
        total_itens = sum(item.quantidade for item in p.produtos)
        
        items_formatados.append({
            "id": p.id,
            "status": p.status,
            "usuario_id": usuario_id,
            "data_criacao": p.data_criacao,
            "valor_total": round(valor_total, 2),
            "total_itens": total_itens
        })
        
    return {
        "items": items_formatados,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total > 0 else 0,
    }


@router.get("/stats/total", summary="Quantidade total de pedidos")
async def total_pedidos():
    """Retorna o total de pedidos cadastrados de maneira nativa e veloz."""
    total = await Pedido.count()
    return {"total_pedidos": total}


@router.get("/stats/por-status", summary="Contagem de pedidos por status")
async def pedidos_por_status():
    """Retorna a quantidade de pedidos agrupados por status via pipeline de agregação."""
    pipeline = [
        {"$group": {"_id": "$status", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$project": {"_id": 0, "status": "$_id", "total": 1}}
    ]
    return await Pedido.aggregate(pipeline).to_list()


@router.get(
    "/usuario/{usuario_id}",
    response_model=List[Pedido],
    summary="Listar pedidos de um usuário",
)
async def listar_pedidos_por_usuario(usuario_id: PydanticObjectId):
    """Lista todos os pedidos de um usuário resolvendo os Links automaticamente se desejado."""
    usuario = await Usuario.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    # No Beanie, consultamos apontando para a referência do objeto Link
    return await Pedido.find(Pedido.usuario.ref.id == usuario_id).sort("-data_criacao").to_list()


@router.get("/ano/{ano}", response_model=List[Pedido], summary="Listar pedidos por ano")
async def listar_pedidos_por_ano(ano: int):
    """Lista os pedidos feitos em um determinado ano usando operadores de data do MongoDB."""
    # Cria uma query comparando a propriedade .year do campo datetime
    return await Pedido.find({
        "$expr": {"$eq": [{"$year": "$data_criacao"}, ano]}
    }).sort("+data_criacao").to_list()


@router.get("/valor", summary="Filtrar pedidos por valor total mínimo")
async def pedidos_acima_do_valor(
    min_valor: float = Query(..., alias="min", description="Valor total mínimo")
):
    """Lista pedidos cujo valor total calculado dos itens embutidos supera o mínimo."""
    # Usamos agregação para criar o campo calculado acumulando preço * quantidade no MongoDB
    pipeline = [
        {
            "$addFields": {
                "valor_total": {
                    "$sum": {
                        "$map": {
                            "input": "$produtos",
                            "as": "item",
                            "in": {"$multiply": ["$$item.preco_unitario", "$$item.quantidade"]}
                        }
                    }
                },
                "total_produtos": {"$sum": "$produtos.quantidade"}
            }
        },
        {"$match": {"valor_total": {"$gt": min_valor}}},
        {"$sort": {"valor_total": -1}},
        {
            "$project": {
                "pedido_id": "$_id",
                "status": 1,
                "usuario_id": "$usuario.$id",  # Extrai do DBRef do Beanie
                "data_criacao": 1,
                "valor_total": {"$round": ["$valor_total", 2]},
                "total_produtos": 1,
                "_id": 0
            }
        }
    ]
    return await Pedido.aggregate(pipeline).to_list()


@router.get(
    "/{pedido_id}/produtos",
    summary="Listar produtos de um pedido com quantidades",
)
async def listar_produtos_do_pedido(pedido_id: PydanticObjectId):
    """Retorna os produtos e suas quantidades contidos nativamente no pedido."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
    # Como o ItemPedido já armazena quantidade e snapshot de forma síncrona, retornamos direto
    return [item.model_dump() for item in pedido.produtos]


@router.get("/{pedido_id}/contagem-produtos", summary="Quantidade de itens num pedido")
async def contar_produtos_pedido(pedido_id: PydanticObjectId):
    """Retorna a soma total das quantidades contidas no array do pedido."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
    total = sum(item.quantidade for item in pedido.produtos)
    
    return {
        "pedido_id": pedido_id, 
        "total_itens": total
    }

@router.get("/{pedido_id}/detalhes", summary="Detalhes completos do pedido")
async def detalhes_pedido(pedido_id: PydanticObjectId):
    """Retorna o pedido com dados completos resolvendo o Link do usuário e somando totais."""
    # fetch_links=True faz o Beanie carregar automaticamente o documento do Usuario associado
    pedido = await Pedido.get(pedido_id, fetch_links=True)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    valor_total = round(sum(item.preco_unitario * item.quantidade for item in pedido.produtos), 2)
    usuario = pedido.usuario

    return {
        "pedido_id": pedido.id,
        "status": pedido.status,
        "data_criacao": pedido.data_criacao,
        "valor_total": valor_total,
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
        } if usuario else None,
        "produtos": [
            {
                "id": item.produto_id,
                "nome": item.nome,
                "preco": item.preco_unitario,
                "quantidade": item.quantidade
            }
            for item in pedido.produtos
        ],
    }


@router.get("/{pedido_id}", response_model=Pedido, summary="Buscar pedido por ID")
async def buscar_pedido(pedido_id: PydanticObjectId):
    """Busca um pedido pelo seu ID (produtos embutidos já vêm inclusos por padrão)."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


@router.post("/", response_model=Pedido, status_code=201, summary="Criar pedido")
async def criar_pedido(dados: PedidoCreate):
    """Cria um novo pedido validando os produtos e gerando o snapshot histórico de preços."""
    # 1. Valida se o usuário existe
    usuario = await Usuario.get(dados.usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    itens_pedido = []

    # 2. Se houver produtos no payload, valida e monta o snapshot de cada um
    if dados.produtos:
        ids_produtos = [p.produto_id for p in dados.produtos]
        
        # Busca todos os produtos correspondentes de uma só vez no MongoDB
        produtos_db = await Produto.find({"_id": {"$in": ids_produtos}}).to_list()
        
        if len(produtos_db) != len(set(ids_produtos)):
            raise HTTPException(
                status_code=404, 
                detail="Um ou mais produtos informados não existem no sistema"
            )

        # Mapeia para facilitar a associação rápida de preço e nome
        mapa_produtos = {p.id: p for p in produtos_db}

        for item_input in dados.produtos:
            produto_original = mapa_produtos[item_input.produto_id]
            
            # Cria o snapshot imutável para o histórico do pedido
            itens_pedido.append(ItemPedido(
                produto_id=str(produto_original.id),
                nome=produto_original.nome,
                preco_unitario=produto_original.preco,
                quantidade=item_input.quantidade
            ))

    # 3. Instancia e salva o pedido usando o Link do Beanie para o Usuário
    pedido = Pedido(
        usuario=usuario,  # O Beanie aceita o documento inteiro para criar o link automaticamente
        status=dados.status,
        produtos=itens_pedido
    )
    await pedido.insert()
    return pedido


@router.post(
    "/{pedido_id}/produtos",
    response_model=Pedido,
    summary="Adicionar produto a um pedido",
)
async def adicionar_produto_ao_pedido(pedido_id: PydanticObjectId, item: ItemPedidoCreate):
    """Adiciona um produto ao pedido ou aumenta a quantidade se já existir no array embutido."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
    produto = await Produto.get(item.produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
        
    # Procura se o produto já existe na lista embutida do pedido
    item_existente = next((p for p in pedido.produtos if p.produto_id == str(item.produto_id)), None)
    
    if item_existente:
        item_existente.quantidade += item.quantidade
    else:
        # Se não existe, cria um snapshot com o preço atual do produto
        pedido.produtos.append(ItemPedido(
            produto_id=str(produto.id),
            nome=produto.nome,
            preco_unitario=produto.preco,
            quantidade=item.quantidade
        ))
        
    await pedido.save()
    return pedido


@router.delete(
    "/{pedido_id}/produtos/{produto_id}",
    response_model=Pedido,
    summary="Remover produto de um pedido",
)
async def remover_produto_do_pedido(pedido_id: PydanticObjectId, produto_id: str):
    """Remove um produto do array embutido de um pedido existente."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
    # Filtra mantendo apenas os produtos que NÃO correspondem ao ID enviado
    produtos_restantes = [p for p in pedido.produtos if p.produto_id != produto_id]
    
    if len(produtos_restantes) == len(pedido.produtos):
        raise HTTPException(status_code=404, detail="Produto não encontrado neste pedido")
        
    pedido.produtos = produtos_restantes
    await pedido.save()
    return pedido


@router.put("/{pedido_id}", response_model=Pedido, summary="Atualizar status do pedido")
async def atualizar_pedido(pedido_id: PydanticObjectId, dados: PedidoUpdate):
    """Atualiza o status de um pedido existente."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
    dados_atualizados = dados.model_dump(exclude_none=True)
    for campo, valor in dados_atualizados.items():
        setattr(pedido, campo, valor)
        
    await pedido.save()
    return pedido


@router.delete("/{pedido_id}", status_code=204, summary="Deletar pedido")
async def deletar_pedido(pedido_id: PydanticObjectId):
    """Remove um pedido do sistema (os itens são apagados juntos de forma atômica)."""
    pedido = await Pedido.get(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
    # Diferente do SQL, não há registros dependentes em tabelas N:M para deletar manualmente.
    await pedido.delete()