# -*-coding: utf8-*-

class GameCard:
    def __init__(self, color, nb):
        self.color = color
        self.nb = nb
    def __str__(self):
        return ("||"+str(self.color)+"|"+str(self.nb)+"||")