FROM python:3.10

# Configurar o proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV NO_PROXY=localhost,127.0.0.1

# Defina o fuso horário
ENV TZ="America/Sao_Paulo"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copiar e instalar as dependências
COPY requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Crie o comando `flower` durante o build
RUN echo '#!/usr/bin/env python3\nfrom flower.__main__ import main\nif __name__ == "__main__":\n    main()' > /usr/local/bin/flower \
    && chmod +x /usr/local/bin/flower

# Expõe a porta padrão do Flower
EXPOSE 5555

# Variável de ambiente para a porta
ENV FLOWER_PORT=5555

