import socket
import sys
import select
from time import sleep
from card import GameCard


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if __name__ == "__main__":
    hote = "localhost"
    port = int(sys.argv[1])
    print("PortRecu", port)
    defausse = None
    deck = list()

    connexion_avec_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connexion_avec_serveur.connect((hote, port))
    print("Connexion établie avec le serveur sur le port {}".format(port))
    connexion_avec_serveur.settimeout(0.2)
    #msg_a_envoyer != b"fin"
    msg_a_envoyer = b""
    start=False
    while True:
        #msg_a_envoyer = input("> ")
        # Peut planter si vous tapez des caractères spéciaux
        #msg_a_envoyer = msg_a_envoyer.encode()
        # On envoie le message
        try:
            msg_recu = connexion_avec_serveur.recv(1024)
        except socket.timeout:
            pass
        else:
            # L'instruction ci-dessous peut lever une exception si le message
            # Réceptionné comporte des accents
            if msg_recu == b'':
                pass
            else:
                print("msg", msg_recu.decode())
                recu = msg_recu.decode()

            if recu[0] == 'd':
                print(recu)
                recu = recu[1:]
                print(recu)
                ldef = recu.split("|")
                print(ldef)
                defausse = GameCard(ldef[0], ldef[1])
                print("def cree", defausse)
            elif recu[0] == 'm':
                start=True
                recu = recu[2:]
                lcar = recu.split("/")
                print(lcar)
                for elt in lcar:
                    elt = elt.split("|")
                    if len(elt) > 0:
                        deck.append(GameCard(elt[0], elt[1]))
            elif recu[0]=='e':
                if recu[1]=='9':
                    print("Plus de carte, tout le monde perd !")
                else:
                    print("Le joueur",recu[1],"gagne la partie !")
                break

        entry = False
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if line:
                entry = True
            else:  # an empty line means stdin has been closed
                print('eof')
                exit(0)
        
        if entry:
            try:
                index = int(input("What would you do ?"))
                assert index >= 0 and index < len(deck)
            except ValueError:
                print("Vous n'avez pas saisi un nombre.")
            except AssertionError:
                print("L'index saisie n'est pas valide.")
            else:
                tosend = "2"+str(deck[index].color)+str(deck[index].nb)
                connexion_avec_serveur.send(tosend.encode())
                no_reply = True
                while no_reply:
                    try:
                        msg_recu = connexion_avec_serveur.recv(1024)
                        assert msg_recu != b''
                    except socket.timeout:
                        print("Nodata")
                        sleep(1)
                    except AssertionError:
                        print("EmptyMsg")
                        sleep(1)
                    else:
                        no_reply = False
                        recu = msg_recu.decode()
                        print("Recu", recu)
                        if recu[0] == "0":
                            deck.pop(index)
                            print("Carte Valide played!")
                        elif recu[0] == "1":
                            deck.append(GameCard(recu[1], recu[2:]))
                            print("Carte invalide played!",
                                  GameCard(recu[1], recu[2:]))
                        else:
                            print("PBLM_RECU")
                        for i in range(len(deck)):
                            print("Deck :", i, deck[i])
        if len(deck)==0 and start:
            #Victoire du joueur
            connexion_avec_serveur.send("4000".encode())

        

    print("Fermeture de la connexion")
    connexion_avec_serveur.close()


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
