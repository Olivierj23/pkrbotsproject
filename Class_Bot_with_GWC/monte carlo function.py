import eval7

def calc_strength(my_hole, board, n_mystery_cards, iterations):
    '''


    '''

    deck = eval7.Deck()
    hole_card = [eval7.Card(card) for card in my_hole]
    board_card = [eval7.Card(card) for card in board]

    for card in hole_card + board_card:
        deck.cards.remove(card)

    score = 0

    for _ in range(iterations):
        deck.shuffle()

        _additional_cards = n_mystery_cards
        _OPP = 2

        draw = deck.peek(_additional_cards + _OPP)

        opp_hole = draw[:_OPP]
        additional_cards = draw[_OPP:]

        our_hand = hole_card + board_card + additional_cards
        opp_hand = opp_hole + board_card + additional_cards

        our_value = eval7.evaluate(our_hand)
        opp_value = eval7.evaluate(opp_hand)

        if our_value > opp_value:
            score += 2

        elif our_value == opp_value:
            score += 1

        else:
            score += 0

    hand_strength = score / (2 * iterations)

    return hand_strength
