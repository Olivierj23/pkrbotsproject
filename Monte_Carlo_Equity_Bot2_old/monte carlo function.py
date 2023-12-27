import eval7


def calc_strength(self, hole, iters, community=[]):
    '''
    Using MC with iterations to evalute hand strength
    Args:
    hole - our hole carsd
    iters - number of times we run MC
    community - community cards
    '''

    deck = eval7.Deck()  # deck of cards
    hole_cards = [eval7.Card(card) for card in hole]  # our hole cards in eval7 friendly format

    # If the community cards are not empty, we need to remove them from the deck
    # because we don't want to draw them again in the MC
    if community != []:
        community_cards = [eval7.Card(card) for card in community]
        for card in community_cards:  # removing the current community cards from the deck
            deck.cards.remove(card)

    for card in hole_cards:  # removing our hole cards from the deck
        deck.cards.remove(card)

    # the score is the number of times we win, tie, or lose
    score = 0

    for _ in range(iters):  # MC the probability of winning
        deck.shuffle()

        # Let's see how many community cards we still need to draw
        if len(community) >= 5:  # red river case
            # check the last community card to see if it is red
            if community[-1][1] == 'h' or community[-1][1] == 'd':
                _COMM = 1
            else:
                _COMM = 0
        else:
            _COMM = 5 - len(community)  # number of community cards we need to draw

        _OPP = 2

        draw = deck.peek(_COMM + _OPP)

        opp_hole = draw[:_OPP]
        alt_community = draw[_OPP:]  # the community cards that we draw in the MC

        if community == []:  # if there are no community cards, we only need to compare our hand to the opp hand
            our_hand = hole_cards + alt_community
            opp_hand = opp_hole + alt_community
        else:

            our_hand = hole_cards + community_cards + alt_community
            opp_hand = opp_hole + community_cards + alt_community

        our_hand_value = eval7.evaluate(our_hand)
        opp_hand_value = eval7.evaluate(opp_hand)

        if our_hand_value > opp_hand_value:
            score += 2

        if our_hand_value == opp_hand_value:
            score += 1
        else:
            score += 0

    hand_strength = score / (2 * iters)  # win probability

    return hand_strength
