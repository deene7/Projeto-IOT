# CONTROLE DO DISPLAY OLED.

from machine import I2C, Pin
import config as c
import ssd1306

class Display:
    def __init__(self):
        i2c = I2C(0, scl=Pin(c.PIN_SCL), sda=Pin(c.PIN_SDA))
        self.oled = ssd1306.SSD1306_I2C(c.OLED_LARGURA, c.OLED_ALTURA, i2c)

    def mostrar(self, mensagem, x=0, y=30):
        self.oled.fill(0)
        self.oled.text("CENTRAL", 0, 0)
        self.oled.hline(0, 13, 128, 1)
        self.oled.text(mensagem, x, y)
        self.oled.show()

    def tela_inicial(self):
        self.mostrar("DIGITE O NUMERO", 3)

    def mostrar_caixa(self, numero):
        self.mostrar("CAIXA: " + str(numero))

    def mostrar_estado(self, numero, estado):
        if estado == "EM_PREPARO":
            self.mostrar(estado, 24)
        elif estado == "PRONTO":
            self.mostrar(estado, 35)

    def caixa_recusada(self):
        self.mostrar("CAIXA RECUSADA", 8)

    def mostrar_erro(self):
        self.mostrar("ERRO!", 45)

    def mostrar_aguardando(self):
        self.mostrar("AGUARDANDO", 24)

