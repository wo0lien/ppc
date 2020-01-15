from kbhitmod import KBHit
from multiprocessing import Lock, Process, Event, Manager, Queue
import threading
import queue
import sysv_ipc
import sys
import select
import tty
import random
from card import GameCard
import socket
from time import sleep


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
        cards = dqueue.get()  # bloquant

        # exiting the thread
        if cards is None:
            break

        print(bcolors.WARNING, "-------------deck--------------")

        for i in range(len(cards)):
            if i != 0:  # si ce n'est pas la premiere carte
                print(cards[i].color, cards[i].nb)

        print(bcolors.OKGREEN, "-------------board--------------")
        print(cards[0].color, cards[0].nb)

        # print(cards)
        dqueue.task_done()  # annonce qu'il a fini le tracardsent


def player(key, deck, event, pioche, defausse, id, port):
    hote = ''
    print(port)
    connexion_principale = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connexion_principale.bind((hote, port))
    connexion_principale.listen(5)
    print("Le serveur écoute à présent sur le port {}".format(port))

    connexion_avec_client, infos_connexion = connexion_principale.accept()
    connexion_avec_client.settimeout(0.1)

    """"msg_recu = b""
    while msg_recu != b"fin":
        msg_recu = connexion_avec_client.recv(1024)
        # L'instruction ci-dessous peut lever une exception si le message
        # Réceptionné comporte des accents
        print(msg_recu.decode())
        connexion_avec_client.send(b"5 / 5")"""

    # liaison avec le displayer
    #display_queue = queue.Queue()
    #disp = threading.Thread(target=displayer, args=(display_queue,))
    # disp.start()

    # creation d'une variable globale
    global playLock, defausseLock
    print("Event", event.is_set())
    # on attend le top
    event.wait()
    # on recupere la defausse
    with defausseLock:
        print("def", defausse)
        ldefausse = defausse[-1]

    mq = sysv_ipc.MessageQueue(key)

    sdef = "d"+str(ldefausse.tosend())
    sdeck = "m"
    for car in deck:
        sdeck += ("/"+str(car.tosend()))
    print(sdef)
    connexion_avec_client.send(sdef.encode())
    print(sdeck)
    sleep(1)
    connexion_avec_client.send(sdeck.encode())

    # kb = KBHit()

    while True:
        # wait une action du joueur OU une action sur le board avec les event
        if event.is_set():
            with defausseLock:
                ldefausse = defausse[-1]
                if ldefausse.color != 'e':
                    sdef = "d"+str(ldefausse.tosend())
                    connexion_avec_client.send(sdef.encode())
                else:
                    sdef=""
                    if ldefausse.nb==id:
                        sdef="e1"
                    elif ldefausse.nb==9:
                        sdef="e9"
                    else:
                        sdef="e0"
                    connexion_avec_client.send(sdef.encode())
                    break
            event.clear()
            
        # Action du joueur:
        try:
            msg_recu = connexion_avec_client.recv(1024)
        except socket.timeout:
            pass
        else:
            playLock.acquire()
            recplay = msg_recu.decode()
            print(recplay)
            if recplay[0] == "2" or recplay[0]=="3":
               # envoie la carte et attend une reponse
                mq.send(recplay.encode())
            elif recplay[0] == "4":
                recplay="40"+str(id)
                mq.send(recplay.encode())
            else:
                print("DontKonowWhatTOdo")

            # wait la reponse
            message, t = mq.receive()
            message = message.decode()
            print("RecMQ", message)
            if message[0] == "0" or message[0] == "1" or message[0]=="3":
                connexion_avec_client.send(message.encode())
            elif message[0]=="4":
                pass
            playLock.release()
        

        # if kb.kbhit():
        #     c = kb.getch()
        #     print(c)
        #     if (int(c) > 0 and int(c) <= len(deck)):
        #         # si l'input fait partie du deck de la personne
        #         pass
        #     else:
        #         print("not a valid card")

        # kb.set_normal_term()

        # handle une modification de la liste

        # if ordre de jouer une carte:
        #   cardindex = cardsaisie
        #   break

    # Fin du serveur
    print("Fermeture de la connexion")
    connexion_avec_client.close()
    connexion_principale.close()


if __name__ == "__main__":

    port = int(sys.argv[1])
    print("Portbase", port)

    with Manager() as manager:

        # on génère la pile de cartes LIFO
        pioche = manager.list()
        defausse = manager.list()

        # queue pour la communication interprocess
        key = 128
        mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)

        # initialisation
        nbJoueurs = 2
        lcarte = list()
        for i in range(10):
            lcarte.append(GameCard("r", i+1))
            lcarte.append(GameCard("b", i+1))

        levent = list()
        lprocess=list()
        for i in range(nbJoueurs):
            playerDeck = list()
            for _ in range(5):
                playerDeck.append(lcarte.pop(random.randint(0, len(lcarte)-1)))
            ev = Event()
            ev.clear()
            levent.append(ev)
            print("Ev", ev.is_set())
            p = Process(target=player, args=(
                key, playerDeck, ev, pioche, defausse, i, port+i))
            lprocess.append(p)
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
            msgrec = message.decode()
            print("MSG:"+msgrec)
            # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher
            if msgrec[0] == "2":
                carteR = GameCard(msgrec[1], msgrec[2:])
                if (carteR.color == defausse[-1].color and (carteR.nb%10 == (defausse[-1].nb-1)%10 or carteR.nb%10 == (defausse[-1].nb+1)%10)) or (carteR.color != defausse[-1].color and carteR.nb == defausse[-1].nb):
                    valid = True
                if valid:
                    defausse.append(carteR)
                    mq.send("0000".encode())
                    for ev in levent:
                        ev.set()
                else:
                    cardpioche = pioche.pop()
                    reply = "1"+str(cardpioche.color)+str(cardpioche.nb)
                    mq.send(reply.encode())
            elif msgrec[0]=="3":
                cardpioche = pioche.pop()
                reply = "3"+str(cardpioche.color)+str(cardpioche.nb)
                mq.send(reply.encode())
            elif msgrec[0]== "4":
                defausse.append(GameCard('e',msgrec[2:]))
                mq.send(msgrec.encode())
                for ev in levent:
                    ev.set()
                break
            
            if len(pioche)==0:
                defausse.append(GameCard('e',9))
                for ev in levent:
                    ev.set()
                break
        
        for p in lprocess:
            p.join()
        mq.remove()
