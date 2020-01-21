from kbhitmod import KBHit
import socket
import sys
import select
from time import sleep, time
from card import GameCard
from displayer import displayer
from threading import Thread
from queue import Queue
import argparse

# kbhit imports
import os
from time import sleep
# Windows
if os.name == 'nt':
    import msvcrt

# Posix (Linux, OS X)
else:
    import sys
    import termios
    import atexit
    from select import select

if __name__ == "__main__":

    kb = KBHit()

    # connexion avec le displayer
    display_queue = Queue()
    displayworker = Thread(target=displayer, args=(display_queue,))
    displayworker.start()

    cards = list()

    # récupération des arguments de la commande
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", "-hn", type=str,
                        help="Server hostname", default="localhost")
    parser.add_argument("--port", "-p", type=int,
                        help="Server listening port", default="12800")
    args = parser.parse_args()

    # handling user inputs
    hote = args.hostname
    port = args.port
    print("PortRecu", port)
    defausse = None
    deck = list()

    # socket de connexion avec le serveur
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((hote, port))

    print("Connexion établie avec le serveur sur le port {}".format(port))
    server_socket.settimeout(0.2)

    #msg_a_envoyer != b"fin"
    msg_a_envoyer = b""
    start = False 
    timout = 15 #valeur du timeout
    time0 = float()

    while True:
        # reception d'un message sur le socket
        try:
            msg_recu = server_socket.recv(1024)
        except socket.timeout:
            pass
        else:
            # decodage du message
            if msg_recu == b'':
                pass
            else:
                recu = msg_recu.decode()
            #Reception de la defausse
            if recu[0] == 'd':
                recu = recu[1:]
                ldef = recu.split("|")
                defausse = GameCard(ldef[0], ldef[1])
            #Reception de la main du joueur
            elif recu[0] == 'm':
                start = True
                time0 = time()
                recu = recu[2:]
                lcar = recu.split("/")

                for elt in lcar:
                    elt = elt.split("|")
                    if len(elt) > 0:
                        deck.append(GameCard(elt[0], elt[1]))
            #Réception de la fin du jeu
            elif recu[0] == 'e':
                display_queue.put([GameCard('e', recu[1])])
                break

            # envoie au displayer
            display_queue.put([defausse] + deck)
            display_queue.join()  # on attend la fin de l'affichage

        entry = False

        # utilisation de la classe kbhit pour un input non bloquant
        if kb.kbhit():
            #Récuperation de la touche préssée sur le clavier
            index = kb.getch()
            try:
                index = ord(index)-97
                assert index >= 0 and index < len(deck)
            except ValueError:
                print("Vous n'avez pas saisi un nombre.")
            except AssertionError:
                print("L'index saisie n'est pas valide.")
            else:
                time0 = time()
                # generation du message a envoyer
                tosend = "2"+str(deck[index].color)+str(deck[index].nb)
                server_socket.send(tosend.encode())

                #attente de la reponse du serveur
                no_reply = True
                while no_reply:
                    try:
                        msg_recu = server_socket.recv(1024)
                        assert msg_recu != b''
                    except socket.timeout:
                        print("Error: Nodata")
                        sleep(1)
                    except AssertionError:
                        print("Error: Message vide")
                        sleep(1)
                    else:
                        no_reply = False
                        recu = msg_recu.decode()
                        #Si la carte reçue est valide on l'enleve du deck
                        if recu[0] == "0":
                            deck.pop(index)
                        #Si la carte reçue est invalide on ajoute au deck la carte reçue
                        elif recu[0] == "1":
                            deck.append(GameCard(recu[1], recu[2:]))

                        else:
                            print("Error: Reception")

                        # envoie au displayer

                        display_queue.put([defausse] + deck)
                        display_queue.join()  # on attend la fin de l'affichage

        if len(deck) == 0 and start:
            # Victoire du joueur
            server_socket.send("4000".encode())


        #Time-out
        if (time()-time0 > timout) and start:
            time0 = time()
            tosend = "3000"
            server_socket.send(tosend.encode())
            no_reply = True
            #attente de la carte en provenance du board
            while no_reply:
                try:
                    msg_recu = server_socket.recv(1024)
                    assert msg_recu != b''
                except socket.timeout:
                    print("Error: Nodata")
                    sleep(1)
                except AssertionError:
                    print("Error: Message vide")
                    sleep(1)
                else:
                    no_reply = False
                    recu = msg_recu.decode()
                    if recu[0] == "3":
                        deck.append(GameCard(recu[1], recu[2:]))
                    else:
                        print("Error: Reception")

                     # envoie au displayer

                    display_queue.put([defausse] + deck)
                    display_queue.join()  # on attend la fin de l'affichage

    display_queue.put(None) # kill le displayer
    kb.set_normal_term()
    print("Fermeture de la connexion")
    server_socket.close()
    displayworker.join()
