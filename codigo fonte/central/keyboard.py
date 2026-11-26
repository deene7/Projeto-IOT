# TECLADO MATRICIAL 4x3.

from machine import Pin
from time import sleep_ms
import config as c

class Teclado:
    TECLAS = (
        ("1", "2", "3"),
        ("4", "5", "6"),
        ("7", "8", "9"),
        ("*", "0", "#")
    )

    def __init__(self):
        self.linhas = [Pin(pino, Pin.OUT, value=1) for pino in c.PIN_LINHAS]
        self.colunas = [Pin(pino, Pin.IN, Pin.PULL_UP) for pino in c.PIN_COLUNAS]

    def ler_tecla(self):
        for i, linha in enumerate(self.linhas):
            linha.value(0)

            for j, coluna in enumerate(self.colunas):
                if coluna.value() == 0:
                    sleep_ms(25)  # Evita leituras duplicadas.
                    if coluna.value() == 0:
                        tecla = self.TECLAS[i][j]

                        while coluna.value() == 0:
                            sleep_ms(10)

                        linha.value(1)
                        sleep_ms(25)
                        return tecla

            linha.value(1)

        return None

