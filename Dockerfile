# Utiliza uma imagem oficial leve do Python
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install uv

# Copia os arquivos de configuração primeiro
COPY pyproject.toml uv.lock ./

# Instala as dependências, gerando a pasta .venv
RUN uv sync

# Copia o resto do código da aplicação
COPY . .

# Ativa explicitamente o ambiente virtual Python inserindo-o no PATH.
# Isso garante que o comando 'uvicorn' seja reconhecido.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Executa o servidor ASGI diretamente através do ambiente ativo
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]