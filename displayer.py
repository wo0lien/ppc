import threading
import queue
from time import sleep

def displayer(dqueue):
    """
    Thread qui sera appelé par le process joueur pour gérer les affichages.
    queue partagée
    """
    while True:
        item = dqueue.get() # bloquant

        # exiting the thread
        if item is None:
            break

        print(item) # much more complex computing comming soon

        dqueue.task_done() # annonce qu'il a fini le traitement

if __name__ == "__main__":
    
    display_queue = queue.Queue()

    displayer = threading.Thread(target=displayer, args=(display_queue,))
    displayer.start()
    
    display_queue.put("coucou les loulous")
    display_queue.join() # on attend la fin du traitement

    print("job done !")
    
    display_queue.put(None)
    