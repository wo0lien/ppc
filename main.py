from multiprocessing import Lock, Process, Event
import threading
import queue
import sysv_ipc
import sys
import select
import tty
import termios
import random

# on génère la pile de cartes LIFO
pioche = list()
defausse = list()

# mutex
playLock = Lock()
defausseLock = Lock()

def displayer(display_queue, display_event, response_event):
    """
    Thread qui sera appelé par le process joueur pour gérer les affichages.
    """
    while True:
        display_event.wait()
        value = display_queue.get()

        print(value) # ensuite on rajoutera le traitement et le socket la dessus

        display_event.clear()
        response_event.set()

def player(key, deck, event):

    # lien avec le thread displayer

    display_queue = queue.Queue()
    display_event = threading.Event()
    response_event = threading.Event()

    displayer = threading.Thread(target="displayer", args=(display_queue, display_event, response_event))
    
    # creation d'une variable globale

    global playLock, defausseLock
    global pioche, defausse 

    # on recupere la defausse

    with defausseLock:
        ldefause = defausse

    mq = sysv_ipc.MessageQueue(key)

    while True:
        while True:
            # wait une action du joueur OU une action sur le board avec les event

            # handle une modification de la liste
            if event.isSet():
                with defausseLock():
                    ldefause = defausse
                event.clear()

            # if ordre de jouer une carte:
            #   cardindex = cardsaisie
            #   break

        cardIndex = 0
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
    nbJoueurs = 2
    lcarte=list()
    for i in range(10):
        lcarte.append(GameCard("r",i+1))
        lcarte.append(GameCard("b",i+1))

    for i in range(nbJoueurs):
        playerDeck=list()
        for i in range(10):
            playerDeck.append(lcarte.pop(random.randint(0, len(lcarte))))
        ev = Event()
        p = Process(target=player, args=(key, playerDeck, ev,))
        p.start()

    # rentre dans le jeu

    while True:
        valid = False
        message, t = mq.receive()
        # on bloque la possibilité de poser des cartes
        value = message.decode()
        # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher
        try:
            carteR=GameCard(value)
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
