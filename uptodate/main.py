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


def player(key, deck, event, defausse, id, port):
    
    #Initialisation de la connexion TCP
    hote = ''
    connexion_principale = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connexion_principale.bind((hote, port))
    connexion_principale.listen(5)
    print("Le serveur écoute à présent sur le port {}".format(port))
    #Attente du client
    connexion_avec_client, _ = connexion_principale.accept()
    connexion_avec_client.settimeout(0.1)

    # creation d'une variable globale
    global playLock, defausseLock
    #print("Event", event.is_set())
    # on attend le feu vert du board pour lancer le jeu
    event.wait()

    # on recupere la defausse
    with defausseLock:
        print("def", defausse)
        ldefausse = defausse[-1]
    #Mise en place de la MessageQueue avec le main process 
    mq = sysv_ipc.MessageQueue(key)

    #Envoie de la defausse et de la main au client TCP
    sdef = "d"+str(ldefausse.tosend())
    sdeck = "m"
    for car in deck:
        sdeck += ("/"+str(car.tosend()))
    connexion_avec_client.send(sdef.encode())
    sleep(1) #attente pour eviter le chevauchement des messages 
    connexion_avec_client.send(sdeck.encode())

    #Boucle principale de jeu
    while True:
        #Verification si une mise a jour du board est disponible 
        if event.is_set(): 
            with defausseLock: 
                ldefausse = defausse[-1]  #recuperation de la dernière carte sur la defausse
                if ldefausse.color != 'e': #si la couleur de la carte vaut 'e' le jeu est termine
                    sdef = "d"+str(ldefausse.tosend())
                    connexion_avec_client.send(sdef.encode()) #envoie de la carte de la defausse au client 
                else:
                    sdef = ""
                    if ldefausse.nb == id:
                        sdef = "e1" #informe le joueur de sa victoire
                    elif ldefausse.nb == 9:
                        sdef = "e9" #informe le joueur de la defaite de tout le monde (=plus de carte dans la picohe)
                    else:
                        sdef = "e0" #informe le joueur de sa defaite
                    connexion_avec_client.send(sdef.encode())
                    break #le jeu est terminé
            event.clear()

        # Reception d'un ordre de jouer du client:
        try:
            msg_recu = connexion_avec_client.recv(1024)
        except socket.timeout:
            pass #pas de message reçu
        else:
            #Verouillage du plateau pour passer l'action du joueur
            playLock.acquire() 
            recplay = msg_recu.decode()
            #print(recplay)

            if recplay[0] == "2" or recplay[0] == "3": #ordre de jouer une carte ou d'en recuperer une de la pioche
                #transmission de la demande au board
                mq.send(recplay.encode())
            elif recplay[0] == "4": #Victoire du client 
                recplay = "40"+str(id)
                mq.send(recplay.encode()) #transmission de la victoire au board
            else:
                print("DontKonowWhatTOdo")

            # attente de la reponse du board
            message, _ = mq.receive()
            message = message.decode()

            #print("RecMQ", message)
            if message[0] == "0" or message[0] == "1" or message[0] == "3":
                connexion_avec_client.send(message.encode())
            elif message[0] == "4":
                pass
            #Deverouillage du plateau
            playLock.release()
            
    # Fin du serveur
    print("Fermeture de la connexion")
    connexion_avec_client.close()
    connexion_principale.close()


if __name__ == "__main__":

    # récupération des arguments de la commande
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int,
                        help="Server listening port", default=12800)
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

        #generation de l'ensemble des cartes du jeu
        lcarte = list()
        for i in range(10):
            lcarte.append(GameCard("r", i+1))
            lcarte.append(GameCard("b", i+1))
        
        #liste des events et process associés aux joueurs
        levent = list()
        lprocess = list()

        #Génération des process player
        for i in range(nbJoueurs):
            #generation aléatoire de la main du joueur
            playerDeck = list()
            for _ in range(5):
                playerDeck.append(lcarte.pop(random.randint(0, len(lcarte)-1)))
            ev = Event()
            ev.clear()
            levent.append(ev)
            p = Process(target=player, args=(
                key, playerDeck, ev, defausse, i, port+i))
            lprocess.append(p)
            p.start()

        #Génération aléatoire de la pioche à partir des cartes récentes
        for i in range(len(lcarte)):
            pioche.append(lcarte.pop(random.randint(0, len(lcarte)-1)))

        #Ajout de la dernière carte à la defausse
        defausse.append(pioche.pop())

        # Informe les process que le jeu est pret
        for ev in levent:
            ev.set()

        while True:
            valid = False
            #le board attend une action d'un joueur 
            message, t = mq.receive()
            msgrec = message.decode()
            #print("MSG:"+msgrec)

            # Si un joueur veut jouer une carte
            if msgrec[0] == "2":
                carteR = GameCard(msgrec[1], msgrec[2:])
                if (carteR.color == defausse[-1].color and (carteR.nb % 10 == (defausse[-1].nb-1) % 10 or carteR.nb % 10 == (defausse[-1].nb+1) % 10)) or (carteR.color != defausse[-1].color and carteR.nb == defausse[-1].nb):
                    valid = True
                if valid:
                    defausse.append(carteR)
                    mq.send("0000".encode())
                    for ev in levent:
                        ev.set()
                else: #Si la carte n'est pas valide une carte de la pioche est envoyé dans la réponse
                    cardpioche = pioche.pop()
                    reply = "1"+str(cardpioche.color)+str(cardpioche.nb)
                    mq.send(reply.encode())
            #Si un joueur a depassé le timer
            elif msgrec[0] == "3":
                cardpioche = pioche.pop()
                reply = "3"+str(cardpioche.color)+str(cardpioche.nb)
                mq.send(reply.encode())
            #Si un joueur a gagné
            elif msgrec[0] == "4":
                defausse.append(GameCard('e', msgrec[2:]))
                mq.send(msgrec.encode())
                for ev in levent:
                    ev.set()
                break
            #Si la pioche est vide, tout le monde perd
            if len(pioche) == 0:
                defausse.append(GameCard('e', 9))
                for ev in levent:
                    ev.set()
                break

        for p in lprocess:
            p.join()
        mq.remove()
