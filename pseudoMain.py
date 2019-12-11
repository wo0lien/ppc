imports

# on génère la pile de cartes LIFO

pioche = list()
defausse = list()

# mutex pour la pioche et le jeu

playLock = Lock()
defausseLock = Lock()


def player(key, deck, event):

    global playLock
    global pioche, defausse

    # on recupere la defausse

    with defausseLock:
        ldefause = defausse

    # connexion a la messageQueue

    mq = sysv_ipc.MessageQueue(key)

    while True:


        while True:
        # wait une action du joueur OU une action sur le board avec les event

            # handle une modification de la liste
            if event.isSet():
                with defausseLock():
                    ldefause = defausse
                event.clear()

	    afficher(defausse[last])
	    afficher(deck)

            if ordre de jouer une carte:
               cardindex = cardsaisie
               break

        # envoie la carte et attend une reponse en lockant le jeu        

        playLock.acquire()

	cardindex.send()
        
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

    global pioche, defausse

    pioche = liste de ("couleur", nombre) entre 1 et 10, rouge et bleu
    nbJoueurs = 4

    for i in range(nbJoueurs):

        playerDeck = [list de tuples ("couleur", nombre) piochés random dans la pioche]
        ev = Event()
        p = Process(target=player, args=(key, playerDeck, ev, ))
        p.start()
    
    # rentre dans le jeu

    while True:

        valid = True

        message, t = mq.receive()
        # on bloque la possibilité de poser des cartes
        carteRecue = message.decode()
        # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher

        valid = carteRecue est valide

        if valid:
            defausse.append(carteRecue)
            mq.send("0".encode())
        else:
            mq.send("1".encode())
	
        # fin du jeu
	with playLock:
	    si pioche.length = 0
            break

    mq.remove()