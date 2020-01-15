import threading
import queue
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

if __name__ == "__main__":
    
    display_queue = queue.Queue()

    displayer = threading.Thread(target=displayer, args=(display_queue,))
    displayer.start()
    
    cards = list()
    for i in range(10):
        cards.append(GameCard("red", i))

    display_queue.put(cards)
    display_queue.join() # on attend la fin du tracardsent
    
    display_queue.put(None)
    