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
import argparse


# mutex
playLock = Lock()
defausseLock = Lock()


def player(key, deck, event, pioche, defausse, id, port):

    hote = ''
    print(port)
    connexion_principale = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connexion_principale.bind((hote, port))
    connexion_principale.listen(5)
    print("Le serveur écoute à présent sur le port {}".format(port))

    connexion_avec_client, _ = connexion_principale.accept()
    connexion_avec_client.settimeout(0.1)

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

    while True:
        # wait une action du joueur OU une action sur le board avec les event
        if event.is_set():
            with defausseLock:
                ldefausse = defausse[-1]
                if ldefausse.color != 'e':
                    sdef = "d"+str(ldefausse.tosend())
                    connexion_avec_client.send(sdef.encode())
                else:
                    sdef = ""
                    if ldefausse.nb == id:
                        sdef = "e1"
                    elif ldefausse.nb == 9:
                        sdef = "e9"
                    else:
                        sdef = "e0"
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
            if recplay[0] == "2" or recplay[0] == "3":
               # envoie la carte et attend une reponse
                mq.send(recplay.encode())
            elif recplay[0] == "4":
                recplay = "40"+str(id)
                mq.send(recplay.encode())
            else:
                print("DontKonowWhatTOdo")

            # wait la reponse
            message, _ = mq.receive()
            message = message.decode()
            print("RecMQ", message)
            if message[0] == "0" or message[0] == "1" or message[0] == "3":
                connexion_avec_client.send(message.encode())
            elif message[0] == "4":
                pass
            playLock.release()

    # Fin du serveur
    print("Fermeture de la connexion")
    connexion_avec_client.close()
    connexion_principale.close()


if __name__ == "__main__":

    # récupération des arguments de la commande
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int,
                        help="Server listening port", required=True)
    args = parser.parse_args()

    port = args.port
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
        lprocess = list()
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
                if (carteR.color == defausse[-1].color and (carteR.nb % 10 == (defausse[-1].nb-1) % 10 or carteR.nb % 10 == (defausse[-1].nb+1) % 10)) or (carteR.color != defausse[-1].color and carteR.nb == defausse[-1].nb):
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
            elif msgrec[0] == "3":
                cardpioche = pioche.pop()
                reply = "3"+str(cardpioche.color)+str(cardpioche.nb)
                mq.send(reply.encode())
            elif msgrec[0] == "4":
                defausse.append(GameCard('e', msgrec[2:]))
                mq.send(msgrec.encode())
                for ev in levent:
                    ev.set()
                break

            if len(pioche) == 0:
                defausse.append(GameCard('e', 9))
                for ev in levent:
                    ev.set()
                break

        for p in lprocess:
            p.join()
        mq.remove()
