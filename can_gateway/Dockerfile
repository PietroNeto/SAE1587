# syntax=docker/dockerfile:1
FROM python:3.10

# Configurações do Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /code

# Copia e instala as dependências
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . /code/