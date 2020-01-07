from multiprocessing import Lock, Process, Event, Manager
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


def player(key, deck, event, pioche, defausse):

    # liaison avec le displayer

    display_queue = queue.Queue()

    disp = threading.Thread(target=displayer, args=(display_queue,))
    disp.start()

    # creation d'une variable globale
    global playLock, defausseLock
    print("Event",event.is_set())
    #on attend le top
    event.wait()
    # on recupere la defausse
    with defausseLock:
        print("def",defausse)
        ldefausse = defausse[0]

    mq = sysv_ipc.MessageQueue(key)

    # kb = KBHit()

    while True:
        # wait une action du joueur OU une action sur le board avec les event

        # if kb.kbhit():
        #     c = kb.getch()
        #     print(c)
        #     if (int(c) > 0 and int(c) <= len(deck)):
        #         # si l'input fait partie du deck de la personne
        #         pass
        #     else:
        #         print("not a valid card")


        # kb.set_normal_term()

        print("Defausse :" + ldefausse)
        # wait une action du joueur OU une action sur le board avec les event

        # handle une modification de la liste
        if event.is_set():
            with defausseLock():
                ldefausse = defausse[-1]
            event.clear()

        # if ordre de jouer une carte:
        #   cardindex = cardsaisie
        #   break
        print("Defausse :"+ldefausse)
        for i in range(len(deck)):
            print("index : "+i+" "+deck[i])
            
        cardIndex = int(input("Select index ?"))
        # envoie la carte et attend une reponse

        playLock.acquire()

        cardenv = mq.encode(deck[cardIndex])
        mq.send(cardenv)

        # wait la reponse
        message, t = mq.receive()
        value = int(message.decode())

        if (value == 1):
            deck.append(pioche.pop())
        else:
            deck.pop(cardIndex)

        playLock.release()


if __name__ == "__main__":

    with Manager() as manager:

        # on génère la pile de cartes LIFO
        pioche = manager.list()
        defausse = manager.list()
        
        # queue pour la communication interprocess
        key = 128
        mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)

        # initialisation
        nbJoueurs = 1
        lcarte=list()
        for i in range(10):
            lcarte.append(GameCard("r",i+1))
            lcarte.append(GameCard("b",i+1))
        
        levent=list()
        for i in range(nbJoueurs):
            playerDeck=list()
            for i in range(5):
                playerDeck.append(lcarte.pop(random.randint(0, len(lcarte)-1)))
            ev = Event()
            ev.clear()
            levent.append(ev)
            print("Ev",ev.is_set())
            p = Process(target=player, args=(key, playerDeck, ev, pioche, defausse))
            p.start()
        for i in range(len(lcarte)):
            pioche.append(lcarte.pop(random.randint(0, len(lcarte)-1)))
        
        defausse.append(pioche.pop())

        # rentre dans le jeu
        for ev in levent:
            ev.set()

        while True:
            valid = False
            message, t = mq.receive()
            # on bloque la possibilité de poser des cartes
            carteR = message.decode()
            print("Carte:"+carteR)
            # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher
            if (carteR.color!=defausse[-1].color and (carteR.nb==defausse[-1].nb-1 or carteR.nb==defausse[-1].nb+1) ) or (carteR.color==defausse[-1].color and  carteR.nb==defausse[-1].nb):
                valid = True
                mq.send("1".encode())
            if valid:
                defausse.append(carteR)
                mq.send("0".encode())
            else:
                mq.send(pioche.pop().encode())

        mq.remove()
