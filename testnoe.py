from card import GameCard
if __name__ == "__main__":
    lcarte=list()
    for i in range(10):
        lcarte.append(GameCard("r",i+1))
        lcarte.append(GameCard("b",i+1))
    print(lcarte[3])