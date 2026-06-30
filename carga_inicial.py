import asyncio
import random
import string
from faker import Faker

# Importação da função que inicializa a conexão com o banco lendo o .env
from database import init_db

# Importação dos modelos do Beanie
from entidades.usuario import Usuario
from entidades.endereço import Endereco
from entidades.loja import Loja
from entidades.produto import Produto
from entidades.pedido import Pedido, ItemPedido

fake = Faker('pt_BR')
TOTAL_REGISTROS = 100

# ---------------------------------------------------------------------
# FUNCOES GERADORAS
# ---------------------------------------------------------------------

def senha_aleatoria(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def cep_falso():
    numero_base = random.randint(10000000, 99999999)
    cep = f"{numero_base:08d}"
    return f"{cep[:5]}-{cep[5:]}"

def gerar_endereco():
    return Endereco(
        rua=fake.street_name(),
        cidade=fake.city(),
        estado=fake.estado_sigla(),
        cep=cep_falso(),
    )

def gerar_usuario():
    return Usuario(
        nome=fake.name(),
        email=fake.email(),
        senha=senha_aleatoria(random.randint(6, 12)),
        endereco=gerar_endereco(),
    )

def gerar_loja():
    return Loja(
        nome_fantasia=fake.company(),
        razao_social=f"{fake.company()} {fake.company_suffix()}",
        cnpj=fake.cnpj(),
        telefone=fake.phone_number(),
        ativa=True,
    )

produtos_base = [
    "Monitor", "Teclado Mecanico", "Mouse Gamer", "Placa de Video",
    "Cadeira Gamer", "Headset", "Memoria RAM", "SSD NVMe",
    "Fonte ATX", "Placa Mae", "Webcam", "Gabinete"
]

def gerar_produto(loja_ref):
    nome_produto = f"{random.choice(produtos_base)} {fake.word().capitalize()}"
    return Produto(
        nome=nome_produto,
        descricao=fake.text(max_nb_chars=100),
        preco=round(random.uniform(50.0, 4000.0), 2),
        estoque=random.randint(0, 300),
        loja=loja_ref
    )

def gerar_pedido(usuario_ref, produtos_selecionados):
    itens_pedido = []
    for produto in produtos_selecionados:
        itens_pedido.append(ItemPedido(
            produto_id=str(produto.id),
            nome=produto.nome,
            preco_unitario=produto.preco,
            quantidade=random.randint(1, 5)
        ))

    return Pedido(
        usuario=usuario_ref,
        status="pendente",
        produtos=itens_pedido,
    )

# ---------------------------------------------------------------------
# SCRIPT DE CARGA
# ---------------------------------------------------------------------

async def executar_carga():
    print("Conectando ao banco de dados...")
    # Inicializa o banco de dados diretamente, lendo a URL do .env
    await init_db()
    print(f"Iniciando a carga de {TOTAL_REGISTROS} registros por entidade diretamente no MongoDB...")

    print("1. Cadastrando Usuários...")
    usuarios = [gerar_usuario() for _ in range(TOTAL_REGISTROS)]
    await Usuario.insert_many(usuarios)

    print("2. Cadastrando Lojas...")
    lojas = [gerar_loja() for _ in range(TOTAL_REGISTROS)]
    await Loja.insert_many(lojas)

    print("3. Cadastrando Produtos...")
    produtos = []
    for _ in range(TOTAL_REGISTROS):
        loja_aleatoria = random.choice(lojas)
        produtos.append(gerar_produto(loja_aleatoria))
    await Produto.insert_many(produtos)

    print("4. Cadastrando Pedidos...")
    pedidos = []
    for _ in range(TOTAL_REGISTROS):
        usuario_aleatorio = random.choice(usuarios)
        tamanho_carrinho = random.randint(1, 5)
        carrinho = random.sample(produtos, k=min(tamanho_carrinho, len(produtos)))
        
        pedidos.append(gerar_pedido(usuario_aleatorio, carrinho))
    
    await Pedido.insert_many(pedidos)

    print("Processo de carga inicial concluído com sucesso!")
    print(f"  Usuários criados: {len(usuarios)}")
    print(f"  Lojas criadas:    {len(lojas)}")
    print(f"  Produtos criados: {len(produtos)}")
    print(f"  Pedidos criados:  {len(pedidos)}")

if __name__ == "__main__":
    # O Beanie exige um loop de eventos assíncrono para rodar
    asyncio.run(executar_carga())