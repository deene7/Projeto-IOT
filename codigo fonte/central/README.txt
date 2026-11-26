CENTRAL IOT - ESP32-C3 / MICROPYTHON / POO

ORGANIZACAO

main.py          Classe Central: coordena o programa.
config.py        Configuracoes de Wi-Fi, MQTT, pinos e OLED.
keyboard.py      Classe Teclado: leitura do teclado matricial 4x3.
display.py       Classe Display: mensagens exibidas no OLED.
wifi_manager.py  Classe WiFiManager: conexao e consulta do Wi-Fi.
mqtt_manager.py  Classe MQTTManager: publicacao e respostas MQTT.
ssd1306.py       Driver original do display OLED.
boot.py          Arquivo opcional de inicializacao.
firmware/        Firmware MicroPython para ESP32-C3.

COMO A POO FOI APLICADA
-----------------------
Cada classe agrupa os dados e as funcoes de uma responsabilidade.

- Central coordena os outros objetos.
- Display controla o OLED.
- Teclado faz a leitura das teclas.
- WiFiManager controla a rede Wi-Fi.
- MQTTManager controla a comunicacao com o servidor FastAPI.

INSTALACAO
----------
1. Grave o firmware da pasta firmware na placa, se necessario.
2. Copie os arquivos .py da pasta principal para a raiz da ESP32-C3.
3. Confira rede, MQTT e pinos em config.py.
5. Execute main.py pelo Thonny.

CONFIGURACAO

Ajuste WIFI_SSID, WIFI_SENHA e os dados MQTT em config.py. Em MQTT_BROKER, informe o IPv4 do computador onde Mosquitto/FastAPI estao rodando.
Se o broker estiver no computador, use o IPv4 local do computador.
Libere a porta MQTT no firewall.

TOPICOS MQTT

Publicacao: iot/central/consulta
Resposta:   iot/central/resposta

Exemplo enviado:
{"caixa":"01","estado":"EM_PREPARO"}

A resposta do servidor FastAPI deve conter a chave booleana "aceito".

TECLADO E REGRAS

Digite o numero da caixa; * envia EM_PREPARO; # envia PRONTO;
Sao validos os numeros de 01 a 99. A tecla 0 digita o zero.
Se voce digitar um terceiro algarismo, ele inicia um novo numero.
O servidor FastAPI/SQLite valida se a caixa existe e esta ativa.

OBSERVACOES

A central aguarda a resposta do servidor FastAPI antes de aceitar outra operacao.
O MQTT pode precisar de reconexao quando a rede oscilar.
