FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ATLAS_DATA=/data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.7.1 && \
    groupadd --gid 10001 atlas && useradd --uid 10001 --gid 10001 --create-home atlas && \
    install -d -o atlas -g atlas /data
COPY . .
USER 10001:10001
