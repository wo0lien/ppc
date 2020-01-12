# -*-coding: utf8-*-

class GameCard:
    def __init__(self, color, nb):
        self.color = str(color)
        self.nb = int(nb)
    
    def __str__(self):
        return ("||"+str(self.color)+"|"+str(self.nb)+"||")
    
    def tosend(self):
        return str(self.color)+"|"+str(self.nb)