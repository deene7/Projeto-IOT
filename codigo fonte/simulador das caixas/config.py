import os

# Configurações do broker MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_PORTA = int(os.getenv("MQTT_BROKER_PORT", "1883"))

# Usa a conta de demonstração cadastrada no broker que acompanha o projeto.
MQTT_USUARIO = os.getenv("MQTT_USERNAME", "servidor_mqtt")
MQTT_SENHA = os.getenv("MQTT_PASSWORD", "1423")

MQTT_CLIENT_ID = "simulador_caixas_python"
MQTT_KEEPALIVE = 60

# Tópicos
TOPICO_COMANDO = "iot/caixas/+/comando"
TOPICO_RESPOSTA = "iot/caixas/+/resposta"
TOPICO_SOLICITACAO = "iot/caixas/{}/solicitacao"
TOPICO_CENTRAL = "iot/central/consulta"
TOPICO_RESPOSTA_CENTRAL = "iot/central/resposta"
