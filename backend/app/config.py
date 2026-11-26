import os
from pathlib import Path

# Raiz do projeto: projeto_iot/
PROJECT_DIR = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(os.getenv("DB_PATH", PROJECT_DIR / "db" / "banco_de_dados.db")).resolve()

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "servidor_mqtt")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "1423")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "fastapi_servidor_iot")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

TOPIC_CENTRAL = "iot/central/consulta"
TOPIC_CENTRAL_RESPONSE = "iot/central/resposta"
TOPIC_BOX_RELEASE = "iot/caixas/+/solicitacao"
