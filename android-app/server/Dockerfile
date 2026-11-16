# ATLAS Go server. Build from android-app/:  docker build -f server/Dockerfile -t atlas-go-server .
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt
# The server imports the app's pure-Python rules (accounts, domain, payments); Kivy is not needed.
COPY atlas_go/__init__.py atlas_go/accounts.py atlas_go/domain.py atlas_go/payments.py atlas_go/
COPY server/ server/
RUN useradd --system --no-create-home atlas
USER atlas
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "--factory", "server.app:from_env", "--host", "0.0.0.0", "--port", "8080"]
