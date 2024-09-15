import random

class CardImg():
    def __init__(self, x, y, image):
        pass

class Player(CardImg):
    def __init__(self, name, card_pos_x, card_pos_y):
        self.name = name
        self.hand = []
        self.softhand = False
        self.isplaying = bool
        self.bjcount = 0
        self.win = bool
        self.card_pos_x = card_pos_x
        self.card_pos_y = card_pos_y
       

class Card:
    rank = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    suit = ['H', 'C', 'D', 'S']



class Deck:
    def __init__(self):
        self.deck = []

    def generate_deck(self):
        for suit in Card.suit:
            for rank in Card.rank:
                card = rank + suit
                self.deck.append(card)
        

    def shuffle(self):
        random.shuffle(self.deck)

    def deal_card(self):
        # Removes the last card in the shuffled deck and returns it
        return self.deck.pop()
