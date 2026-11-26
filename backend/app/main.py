from contextlib import asynccontextmanager
import logging
import re

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from . import database
from .mqtt_service import MQTTService, normalizar_caixa

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.inicializar_banco()
    mqtt_service.start()
    yield
    mqtt_service.stop()


app = FastAPI(
    title="API do Projeto IoT",
    description="Backend para gerenciamento de caixas, banco SQLite e comunicação MQTT dos ESP32.",
    version="1.0.0",
    lifespan=lifespan,
)


class CaixaCreate(BaseModel):
    numero_caixa: str = Field(..., examples=["04"])


class AtivacaoUpdate(BaseModel):
    ativa: bool


@app.get("/", tags=["Sistema"])
def raiz():
    return {"projeto": "Projeto IoT", "api": "FastAPI", "documentacao": "/docs"}


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "online", "mqtt_conectado": mqtt_service.conectado, "banco": str(database.DATABASE_PATH) if hasattr(database, 'DATABASE_PATH') else "SQLite"}


@app.get("/caixas", tags=["Caixas"])
def caixas():
    return database.listar_caixas()


@app.get("/caixas/{numero}", tags=["Caixas"])
def caixa(numero: str):
    numero_ok = normalizar_caixa(numero)
    if not numero_ok:
        raise HTTPException(400, "Número inválido. Use 01 a 99.")
    resultado = database.obter_caixa(numero_ok)
    if resultado is None:
        raise HTTPException(404, "Caixa não cadastrada.")
    return resultado


@app.post("/caixas", status_code=201, tags=["Caixas"])
def cadastrar_caixa(dados: CaixaCreate):
    numero = normalizar_caixa(dados.numero_caixa)
    if numero is None:
        raise HTTPException(400, "Número inválido. Use 01 a 99.")
    if database.obter_caixa(numero) is not None:
        raise HTTPException(409, "Essa caixa já está cadastrada.")
    database.cadastrar_caixa(numero)
    return database.obter_caixa(numero)


@app.patch("/caixas/{numero}/ativacao", tags=["Caixas"])
def alterar_ativacao(numero: str, dados: AtivacaoUpdate):
    numero_ok = normalizar_caixa(numero)
    if numero_ok is None:
        raise HTTPException(400, "Número de caixa inválido.")
    if not database.definir_ativa(numero_ok, dados.ativa):
        raise HTTPException(404, "Caixa não cadastrada.")
    return database.obter_caixa(numero_ok)


@app.get("/historico", tags=["Histórico"])
def historico(numero_caixa: str | None = None, limite: int = Query(default=200, ge=1, le=1000)):
    numero = None
    if numero_caixa is not None:
        numero = normalizar_caixa(numero_caixa)
        if numero is None:
            raise HTTPException(400, "Número de caixa inválido.")
    return database.listar_historico(numero, limite)


@app.get("/mqtt/status", tags=["MQTT"])
def status_mqtt():
    return {"conectado": mqtt_service.conectado}
