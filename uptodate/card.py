# -*-coding: utf8-*-
class GameCard:
    """
    La classe gamecard permet le transport facilité des données entre les threads client et displayer
    """

    def __init__(self, color, nb):
        """
        Constructeur iinitialisant une nouvelle carte a partir de 2 parametres
        Parameters:
            color (string): couleur de la carte r pour red ou b pour blue
            nb (int): valeur de la carte
        """
        self.color = str(color)
        self.nb = int(nb)
        
    def __str__(self):
        """Affichage d'une carte - utilisé pour le debug"""
        return ("||"+str(self.color)+"|"+str(self.nb)+"||")

    def tosend(self):
        """Fonction qui genere un code string pour la communication avec le board"""
        return str(self.color)+"|"+str(self.nb)
