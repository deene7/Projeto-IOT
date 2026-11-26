# Notificador de pedidos prontos

Projeto IoT para avisar o cliente quando seu pedido de comida estiver pronto. O atendente registra o preparo e marca o pedido como pronto na central. O sistema encaminha o aviso à caixa identificada pelo número informado. Na montagem final, um ESP32 na caixa acionará o motor de vibração.

A central física já tem firmware MicroPython para ESP32-C3. O firmware da caixa vibratória está em desenvolvimento. A central e a caixa podem ser simuladas no Windows, onde um indicador piscando representa a vibração.

## Como funciona

1. O atendente digita o número da caixa e registra o preparo com `*`.
2. Quando o pedido fica pronto, o atendente digita o mesmo número e confirma com `#`.
3. A central publica a solicitação no Mosquitto. O backend FastAPI valida se a caixa está cadastrada e ativa, grava o estado e o histórico no SQLite e publica o comando para a caixa.
4. Ao receber `PRONTO`, a caixa virtual pisca. O botão **Liberar caixa** solicita o retorno ao estado `NAO_USADA`, para que ela possa ser utilizada em outro pedido.

O número da caixa identifica o pedido em atendimento. São aceitos números de **01 a 99**, incluindo **10**, **20** e **90**.

## Executar no Windows sem os ESP32

**Pré-requisitos** — Windows e Python 3.10 ou superior no PATH, com Tkinter. O Mosquitto para Windows acompanha o projeto.

1. Na raiz do projeto, execute `start.bat`. Na primeira execução, ele cria a `.venv` e instala as dependências. Mantenha abertas as janelas do Mosquitto e do FastAPI.
2. Abra outro PowerShell na **mesma pasta** e execute:

   ```powershell
   & ".\.venv\Scripts\python.exe" ".\codigo fonte\simulador das caixas\main.py"
   ```

3. Aguarde **Conectado ao Mosquitto**. Digite **01**, clique em **Registrar preparo (*)** e aguarde a resposta do backend.
4. Clique em **Marcar pronto (#)**. O indicador da caixa **01** deve piscar. Clique em **Liberar caixa** na janela da caixa para concluir o teste.

As janelas **01**, **02** e **03** abrem automaticamente. **Abrir caixa** exibe ou traz para a frente a janela virtual do número digitado. Para usar um número novo, cadastre-o primeiro pela API.

Se o PowerShell informar que o Python da `.venv` não foi encontrado, confira com `Get-Location` se o terminal está na raiz do projeto e se a instalação pelo `start.bat` terminou.

## API e cadastro de caixas

Com o backend rodando, abra a [documentação interativa](http://127.0.0.1:8000/docs). Para cadastrar a caixa **10**, abra `POST /caixas`, clique em **Try it out**, informe o JSON abaixo e clique em **Execute**.

```json
{"numero_caixa": "10"}
```

| Rota | Operação |
| --- | --- |
| `GET /health` | Mostra o estado do backend e da conexão MQTT |
| `GET /caixas` | Lista as caixas cadastradas e seus estados |
| `GET /caixas/{numero}` | Consulta uma caixa |
| `POST /caixas` | Cadastra uma caixa |
| `PATCH /caixas/{numero}/ativacao` | Ativa ou desativa uma caixa |
| `GET /historico` | Consulta o histórico de estados |

## Central física

A central usa um **ESP32-C3**, um teclado matricial **4×3** e um OLED **SSD1306** via I²C.

1. Grave o MicroPython compatível com a placa. O projeto inclui uma imagem para ESP32-C3 na pasta `codigo fonte/central/firmware/`.
2. Instale a biblioteca `umqtt.simple` e copie os arquivos Python de [central](codigo%20fonte/central/) para a raiz da placa.
3. Em [config.py](codigo%20fonte/central/config.py), configure o Wi-Fi, os pinos e uma conta cadastrada no broker. Em `MQTT_BROKER`, informe o IPv4 do computador na rede local. A porta MQTT padrão é **1883**.
4. Reinicie a placa para executar `main.py`. Use `*` para registrar preparo e `#` para marcar pronto. A tecla `0` digita zero. Um terceiro algarismo inicia um novo número.

A central física pode ser testada com a caixa virtual usando o mesmo broker e backend.

## Tópicos MQTT

| Tópico | Quem publica | Conteúdo |
| --- | --- | --- |
| `iot/central/consulta` | Central | Número da caixa e estado `EM_PREPARO` ou `PRONTO` |
| `iot/central/resposta` | Backend | Aceite ou recusa da solicitação |
| `iot/caixas/{numero}/comando` | Backend | Estado enviado à caixa |
| `iot/caixas/{numero}/solicitacao` | Caixa | Solicitação de liberação com estado `NAO_USADA` |
| `iot/caixas/{numero}/resposta` | Backend | Aceite ou recusa da liberação |

A resposta à central confirma que o backend registrou o estado. A versão atual ainda precisa de confirmação de acionamento pela caixa e de recuperação do aviso após perda de conexão.

## Estrutura do projeto

```text
Projeto IOT/
├── backend/app/                    # FastAPI, MQTT e SQLite
├── codigo fonte/
│   ├── central/                    # Código MicroPython e imagem para ESP32-C3
│   └── simulador das caixas/        # Central e caixas virtuais em Tkinter
├── db/                             # Banco SQLite
├── mosquitto/                      # Broker MQTT para Windows e configuração
├── requirements.txt
└── start.bat
```
