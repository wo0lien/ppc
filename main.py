from multiprocessing import Lock, Process, Event
import threading
import queue
import sysv_ipc
import sys
import select
import tty
import random
from card import GameCard

# KBHit

import os

# Windows
if os.name == 'nt':
    import msvcrt

# Posix (Linux, OS X)
else:
    import sys
    import termios
    import atexit
    from select import select

from kbhitmod import KBHit

# on génère la pile de cartes LIFO
pioche = list()
defausse = list()

# mutex
playLock = Lock()
defausseLock = Lock()

# colors pour un zoli terminals

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def displayer(dqueue):
    """
    Thread qui sera appelé par le process joueur pour gérer les affichages.
    queue partagée qui envoie a chaque fois une liste de GameCard, la premiere est celle de la pioche, les suivantes sont celles de la main du joueur
    """
    while True:
        cards = dqueue.get() # bloquant

        # exiting the thread
        if cards is None:
            break
        
        print(bcolors.WARNING, "-------------deck--------------")

        for i in range(len(cards)):
            if i != 0: # si ce n'est pas la premiere carte
                print(cards[i].color, cards[i].nb)

        print(bcolors.OKGREEN, "-------------board--------------")
        print(cards[0].color, cards[0].nb)

        # print(cards)
        dqueue.task_done() # annonce qu'il a fini le tracardsent


def player(key, deck, event):

    # liaison avec le displayer

    display_queue = queue.Queue()

    displayer = threading.Thread(target=displayer, args=(display_queue,))
    displayer.start()

    # creation d'une variable globale

    global playLock, defausseLock
    global pioche, defausse 

    # on recupere la defausse

    with defausseLock:
        ldefausse = defausse

    mq = sysv_ipc.MessageQueue(key)

    kb = KBHit()

    while True:
        
        while True:
            # wait une action du joueur OU une action sur le board avec les event

            if kb.kbhit():
                c = kb.getch()
                if ord(c) == 27: # ESC
                    break
                print(c)

            # handle une modification de la liste
            if event.is_set():
                with defausseLock():
                    ldefausse = defausse
                event.clear()

        kb.set_normal_term()

        print("Defausse :" + ldefausse)
        for i in range(len(deck)):
            print(deck[i])
            
        cardIndex = int(input())
        # envoie la carte et attend une reponse

        playLock.acquire()
        # wait la reponse
        message, t = mq.receive()
        value = int(message.decode())

        if (value == 1):
            deck.append(pioche.pop())
        else:
            deck.pop(cardIndex)

        playLock.release()


if __name__ == "__main__":

    # queue pour la communication interprocess

    key = 128
    mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)

    # initialisation
    nbJoueurs = 1
    lcarte=list()
    for i in range(10):
        lcarte.append(GameCard("r",i+1))
        lcarte.append(GameCard("b",i+1))

    for i in range(nbJoueurs):
        playerDeck=list()
        for i in range(5):
            playerDeck.append(lcarte.pop(random.randint(0, len(lcarte)-1)))
        ev = Event()
        p = Process(target=player, args=(key, playerDeck, ev,))
        p.start()
    for i in range(len(lcarte)):
        pioche.append(lcarte.pop(random.randint(0, len(lcarte)-1)))
    
    defausse.append(pioche.pop())

    # rentre dans le jeu

    while True:
        valid = False
        message, t = mq.receive()
        # on bloque la possibilité de poser des cartes
        value = message.decode()
        # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher
        try:
            carteR = GameCard(value,1)
        except TypeError:
            print("NotACard")
        else:
            if (carteR.color!=defausse[-1].color and (carteR.nb==defausse[-1].nb-1 or carteR.nb==defausse[-1].nb+1) ) or (carteR.color==defausse[-1].color and  carteR.nb==defausse[-1].nb):
                valid = True
            if valid:
                defausse.append(carteR)
                mq.send("0".encode())
            else:
                mq.send(pioche.pop().encode())

    mq.remove()
