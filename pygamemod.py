import pygame
from pygame.locals import *


if __name__ == "__main__":

    pygame.init()

    done = False

    while not done:

        pygame.event.pump()
        keys = pygame.key.get_pressed()
        # if keys[K_ESCAPE]:
        #     done = True

        print(keys)