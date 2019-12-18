from multiprocessing import Lock, Process, Event
import sysv_ipc
import sys
import select
import tty
import termios

# on génère la pile de cartes LIFO
pioche = list()
defausse = list()

# mutex pour les 2 piles de cartes
playLock = Lock()
defausseLock = Lock()


def player(key, deck, event):

    global playLock, defausseLock
    global pioche, defausse
    ldefausse = carte() #copie locale de la defausse 

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

    #initialisation
    nbJoueurs = 4

    for i in range(nbJoueurs):

        playerDeck = [("red", 4), ("blue",2), ("red", 6), ("red", 1)]
        ev = Event()
        p = Process(target=player, args=(key, playerDeck, ev, ))
        p.start()
    
    # rentre dans le jeu

    while True:

        valid = True

        message, t = mq.receive()
        # on bloque la possibilité de poser des cartes
        value = message.decode()
        # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher
        carteRecue = ("red", 10)

        # valid = carte est valide

        if valid:
            defausse.append(carteRecue)
            mq.send("0".encode())
        else:
            mq.send("1".encode())

    mq.remove()
