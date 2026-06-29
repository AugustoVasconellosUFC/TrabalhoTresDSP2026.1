import httpx
import random
import string
import numpy as np
from faker import Faker

fake = Faker('pt_BR')

# URL base da API
URL_API = "http://127.0.0.1:8000"
TOTAL_REGISTROS = 100

# ---------------------------------------------------------------------
# FUNCOES GERADORAS
# ---------------------------------------------------------------------

def senha_aleatoria(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def gerar_usuario():
    return {
        "nome": fake.name(),
        "email": fake.email(),
        "senha": senha_aleatoria(random.randint(6, 12))
    }

def gerar_endereco(usuarios_ids):
    def cep_falso():
        numero_base = random.randint(10000000, 99999999)
        cep = f"{numero_base:08d}"
        return f"{cep[:5]}-{cep[5:]}"
    
    return {
        "rua": fake.street_name(),
        "cidade": fake.city(),
        "estado": fake.estado_sigla(),
        "cep": cep_falso(),
        "usuario_id": random.choice(usuarios_ids)
    }

def gerar_loja():
    return {
        "nome": fake.company(),
        "email": fake.company_email(),
        "senha": senha_aleatoria(random.randint(6, 12))
    }

produtos_base = [
    "Monitor", "Teclado Mecanico", "Mouse Gamer", "Placa de Video",
    "Cadeira Gamer", "Headset", "Memoria RAM", "SSD NVMe",
    "Fonte ATX", "Placa Mae", "Webcam", "Gabinete"
]

def gerar_produto(lojas_ids):
    nome_produto = f"{random.choice(produtos_base)} {fake.word().capitalize()}"
    return {
        "nome": nome_produto,
        "descricao": fake.text(max_nb_chars=100),
        "preco": round(random.uniform(50.0, 4000.0), 2),
        "estoque": random.randint(0, 300),
        "loja_id": random.choice(lojas_ids)
    }

def gerar_pedido(usuarios_ids, produtos_ids):
    tamanho_carrinho = random.randint(1, 5)
    carrinho = random.sample(produtos_ids, k=min(tamanho_carrinho, len(produtos_ids)))

    return {
        "usuario_id": random.choice(usuarios_ids),
        "status": "pendente",
        "produto_ids": carrinho
    }

# ---------------------------------------------------------------------
# SCRIPT DE CARGA
# ---------------------------------------------------------------------

def executar_carga():
    print(f"Iniciando a carga de {TOTAL_REGISTROS} registros por tabela via API...")
    
    ids_usuarios = []
    ids_lojas = []
    ids_produtos = []
    
    with httpx.Client(timeout=30.0) as client:
        
        print("1. Cadastrando Usuarios...")
        for _ in range(TOTAL_REGISTROS):
            resp = client.post(f"{URL_API}/usuarios/", json=gerar_usuario())
            if resp.status_code in [200, 201]:
                ids_usuarios.append(resp.json().get("id"))

        print("2. Cadastrando Lojas...")
        for _ in range(TOTAL_REGISTROS):
            resp = client.post(f"{URL_API}/lojas/", json=gerar_loja())
            if resp.status_code in [200, 201]:
                ids_lojas.append(resp.json().get("id"))

        if not ids_usuarios or not ids_lojas:
            print("Erro fatal: Nao foi possivel criar as entidades base.")
            return

        print("3. Cadastrando Enderecos...")
        for _ in range(TOTAL_REGISTROS):
            client.post(f"{URL_API}/enderecos/", json=gerar_endereco(ids_usuarios))

        print("4. Cadastrando Produtos...")
        for _ in range(TOTAL_REGISTROS):
            resp = client.post(f"{URL_API}/produtos/", json=gerar_produto(ids_lojas))
            if resp.status_code in [200, 201]:
                ids_produtos.append(resp.json().get("id"))

        if not ids_produtos:
            print("Erro fatal: Nao foi possivel criar produtos.")
            return

        print("5. Cadastrando Pedidos...")
        for _ in range(TOTAL_REGISTROS):
            client.post(f"{URL_API}/pedidos/", json=gerar_pedido(ids_usuarios, ids_produtos))

    print("Processo de carga inicial concluido.")

if __name__ == "__main__":
    executar_carga()