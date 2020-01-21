import threading
import queue
from time import sleep
from card import GameCard
from art import *
import os


class bcolors:
    """
    Class used to change the terminal colors
    """
    BLACK = '\u001b[30m'
    BLUE = '\033[94m'
    CYAN = '\u001b[36m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    WHITE = '\u001b[37m'

spaces = [" ","   ","   ","    ","   ","   ","   ","   ","   ","     "]

def displayer(dqueue):
    """
    Thread qui sera appelé par le process joueur pour gérer les affichages.
    queue partagée qui envoie a chaque fois une liste de GameCard, la premiere est celle de la pioche, les suivantes sont celles de la main du joueur
    """
    while True:
        # attends une demande d'affichage
        cards = dqueue.get()  # bloquant

        # exiting the thread if None is sent
        if cards is None:
            break

        reds = list()
        blues = list()

        # enleve la premiere carte de cards car cest la defausse
        defausse = cards.pop(0)

        # affichage de fin de jeu si la couleur de la carte est "e"
        if defausse.color == 'e':
            if defausse.nb == 1:
                os.system('clear')
                print(bcolors.OKGREEN)
                tprint("END")
                tprint('\n')
                tprint("YOU  WIN !")
                break
            elif defausse.nb == 0:
                os.system('clear')
                print(bcolors.RED)
                tprint("END")
                tprint('\n')
                tprint("YOU  LOOSE...")
                break
            else:
                os.system('clear')
                print(bcolors.RED)
                tprint("END")
                tprint('\n')
                tprint("EVERYBODY  LOOSE...")
                break

        # on trie les cartes restantes par couleur
        for card in cards:
            if (card.color == "r"):
                reds.append(card)
            else:
                blues.append(card)

        # display
        os.system('clear')

        # affichage de la defausse
        if (defausse.color == "r"):
            print(bcolors.ORANGE)
        else:
            print(bcolors.CYAN)

        tprint(str(defausse.nb))  # fonction de la lib art

        # affichage des cartes rouges
        print(bcolors.RED)
        redsum = ""
        redindexes = ""
        i = 0
        # recuperation des indexs des cartes rouges
        for card in cards:
            if (card.color == "r"):
                redindexes += spaces[card.nb-1] + str(chr(i+97)+ spaces[card.nb-1] + "   ")
            i += 1
        for card in reds:
            redsum += "   " + str(card.nb)
        if (redsum != ""):
            print(redindexes)
            tprint(redsum)

        # affichage des cartes bleues
        print(bcolors.BLUE)
        bluesum = ""
        blueindexes = ""
        i = 0
        for card in cards:
            if (card.color == "b"):
                blueindexes += spaces[card.nb-1] + str(chr(i+97) + spaces[card.nb-1] + "   ")
            i += 1
        for card in blues:
            bluesum += "   " + str(card.nb)
        if (bluesum != ""):
            tprint(bluesum)
            print(blueindexes)

        print(bcolors.WHITE)

        dqueue.task_done()  # annonce qu'il a fini
