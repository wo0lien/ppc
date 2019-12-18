imports

# on génère la pile de cartes LIFO

pioche = list()
defausse = list()

# mutex pour la pioche et le jeu

playLock = Lock()
defausseLock = Lock()

#variable pour designer le vainqueur
vfin = -1 


def player(key, deck, event, idjoueur):

    global playLock
    global pioche, defausse
    global vfin

    # on recupere la defausse
    with defausseLock:
        ldefause = defausse

    # connexion a la messageQueue
    mq = sysv_ipc.MessageQueue(key)
    fini = False
    while fini==False:
        # wait une action du joueur OU une action sur le board avec les event

        # handle une modification de la situation du jeu
        if event.isSet():
            if vfin != -1:
                fini=True
                break
            with defausseLock():
                ldefause = defausse #on recupere une copie locale de la defausse pour l'affichage du plateau
            event.clear()
        afficher(ldefause)
        afficher(deck)

        if ordre valide de jouer une carte:
            cardindex = cardsaisie.index
            #on essaie de jouer si personne n'est deja en train de jouer
            if playLock.acquire(0)==1:
                # envoie la carte et attend une reponse en lockant le jeu      
                message="2"+Char(cardsaisie.couleur)+String(cardsaisie.val)
                message.encode()
                message.send()
                # wait la reponse
                message, t = mq.receive():


                recu = String(message.decode())
                if (recu[0] == "1"):
                    deck.append(pioche.pop())
                else if :
                    deck.pop(cardIndex)
            
                playLock.release()
            else:
                affichage.jeuimpossible()
        
        if deck.length()==0:
            with playLock:
                message="40"+String(idjoueur)
                message.encode()
                message.send()
                # wait la reponse
                message, t = mq.receive():
            break

    if vfin==0:
        affichage.finsansvainqueur()
    else:
        affichage.finvainqueur(vfin)


if __name__ == "__main__":

    # queue pour la communication interprocess
    key = 128
    mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)
    levent=list()
    lthread=list()

    #initialisation
    global pioche, defausse
    pioche = liste de ("couleur", nombre) entre 1 et 10, rouge et bleu
    nbJoueurs = 3

    for i in range(nbJoueurs):
        playerDeck = [list de tuples ("couleur", nombre) piochés random dans la pioche]
        ev = Event()
        levent.append(ev)
        p = Process(target=player, args=(key, playerDeck, ev, i))
        p.start()
        lthread.append(p)
    
    # rentre dans le jeu
    while True:
        message, t = mq.receive()
        # on bloque la possibilité de poser des cartes
        messageRecu = message.decode()
        # Si c'est valide ou non on renvoie dans la queue le nombre de cartes a piocher
        if message[0]=="2":
            valid = carteRecue.isValide() #on regarde si la carte recu peut être jouée 
            if valid:
                defausse.append(carteRecue)
                mq.send("0000".encode())
            else:
                piochee=pioche.pop()
                messageEnvoi="1"+String(piochee.couleur)+String(piochee.val)
                mq.send(messageEnvoi.encode())
        else if message[0]=="3":
            piochee=pioche.pop()
            messageEnvoi="1"+String(piochee.couleur)+String(piochee.val)
            mq.send(messageEnvoi.encode())
        else if message[0]=="4":
            vfin=int(message[2]+message[3])
            for elt in levent:
                elt.set()
            mq.send("0000".encode())
            break

        
        # fin du jeu
	    with playLock:
	        if pioche.length == 0:
                v.fin=0
                for elt in levent:
                    elt.set()
                break
    for elt in lthread:
        elt.join()
    mq.remove()

        

 