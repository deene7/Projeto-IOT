# Projeto IoT — Arquitetura Portátil

Sistema IoT composto por **Broker MQTT (Mosquitto)**, **Backend FastAPI + SQLite**, **Simulador de Caixas (Tkinter)** e **Firmware/Código MicroPython da Central (ESP32-C3)**.

## Estrutura de Pastas

```
projeto_iot/
├── start.bat                
├── .env.example             
├── .gitignore               
├── backend/                 
│   └── app/
│       ├── config.py
│       ├── database.py
│       ├── main.py
│       └── mqtt_service.py
├── codigo fonte/
│   ├── caixa/
│   ├── central/
│   └── simulador das caixa/
├── mosquitto/               
├── db/
└── firmware/
```

## Como simular no Windows sem os ESP32

1. Execute **`start.bat`** para iniciar o Mosquitto e o FastAPI. Na configuração padrão, a primeira execução cria a `.venv` e instala as dependências.
2. Com o servidor aberto, execute em outro terminal PowerShell, a partir da raiz do projeto:

   ```powershell
   & ".\.venv\Scripts\python.exe" ".\codigo fonte\simulador das caixas\main.py"
   ```

3. Na janela principal, digite **01**. Clique em **Registrar preparo (*)** e, após a resposta, em **Marcar pronto (#)**.
4. Na janela da caixa **01**, o indicador pisca quando chega o comando `PRONTO`. Clique em **Liberar caixa** para voltar ao estado disponível.

A central virtual usa o mesmo protocolo MQTT da central física. O indicador piscando representa a vibração. O teste cobre o fluxo de mensagens e estados, enquanto o teclado, o OLED e o motor precisam ser testados nas placas. A API pode ser consultada em `http://127.0.0.1:8000/docs`.


## Configuração da Central ESP32-C3
Edite `central/config.py` com o SSID/senha do Wi-Fi e informe em `MQTT_BROKER` o **IPv4 local** do computador onde o servidor está em execução.
