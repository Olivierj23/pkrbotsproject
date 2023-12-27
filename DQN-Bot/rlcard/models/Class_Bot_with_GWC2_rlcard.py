''' Limit Hold 'em rule model
'''
import rlcard
from rlcard.models.model import Model
import random
import eval7
from enum import Enum
from rlcard.games.nolimitholdem.round import Action



def calc_strength(hole, iters, community = []):
    '''
    Using MC with iterations to evalute hand strength
    Args:
    hole - our hole carsd
    iters - number of times we run MC
    community - community cards
    '''

    deck = eval7.Deck() # deck of cards
    hole_cards = [eval7.Card(card) for card in hole] # our hole cards in eval7 friendly format


    # If the community cards are not empty, we need to remove them from the deck
    # because we don't want to draw them again in the MC
    if community != []:
        community_cards = [eval7.Card(card) for card in community]
        for card in community_cards: #removing the current community cards from the deck
            deck.cards.remove(card)

    for card in hole_cards: #removing our hole cards from the deck
        deck.cards.remove(card)

    #the score is the number of times we win, tie, or lose
    score = 0

    for _ in range(iters): # MC the probability of winning
        deck.shuffle()

        #Let's see how many community cards we still need to draw
        if len(community) >= 5: #red river case
            #check the last community card to see if it is red
            if community[-1][1] == 'h' or community[-1][1] == 'd':
                _COMM = 1
            else:
                _COMM = 0
        else:
            _COMM = 5 - len(community) # number of community cards we need to draw

        _OPP = 2

        draw = deck.peek(_COMM + _OPP)

        opp_hole = draw[:_OPP]
        alt_community = draw[_OPP:] # the community cards that we draw in the MC


        if community == []: # if there are no community cards, we only need to compare our hand to the opp hand
            our_hand = hole_cards  + alt_community
            opp_hand = opp_hole  + alt_community
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

    hand_strength = score/(2*iters) # win probability

    return hand_strength

class ClassBotwithGWC2Agent(object):
    ''' Reimplementation of our best bot Class Bot with GWC2
    '''

    def __init__(self):
        self.use_raw = True


    def eval_step(self, state):
        ''' Step for evaluation. The same to step
        '''
        return self.step(state), []

    @staticmethod
    def step(state):
        ''' Predict the action when given raw state. A simple rule-based AI.
        Args:
            state (dict): Raw state from the game

        Returns:
            action (str): Predicted action
        '''
        legal_actions = state['raw_legal_actions']
        state = state['raw_obs']
        pot_total = sum(state['all_chips'])
        continue_cost = max(0, state['all_chips'][1] - state['all_chips'][0])

        hand = state['hand']
        temp_hand = []
        for card in hand:
            temp_hand.append(card[1] + card[0].lower())
        hand = temp_hand


        public_cards = state['public_cards']
        temp_public_cards = []
        for card in public_cards:
            temp_public_cards.append(card[1] + card[0].lower())
        public_cards = temp_public_cards

        my_action = legal_actions[0]

        _MONTE_CARLO_ITERS = 100

        # running monte carlo simulation when we have community cards vs when we don't
        if len(public_cards) < 3:
            strength = calc_strength(hand, _MONTE_CARLO_ITERS)
        else:
            strength = calc_strength(hand, _MONTE_CARLO_ITERS, public_cards)

        pot_odds = continue_cost / (pot_total + continue_cost)


        # raise logic
        if len(public_cards) < 3:  # preflop
            raise_amount = Action.RAISE_HALF_POT

        else:  # postflop
            raise_amount = Action.RAISE_POT


        if repr(raise_amount) in repr(legal_actions):
            temp_action = raise_amount
        elif repr(Action.CHECK_CALL) in repr(legal_actions):
            temp_action = Action.CHECK_CALL
        else:
            temp_action = Action.FOLD

        if continue_cost > 0:
            # _SCARY = 0.35 / (1 + (math.e) ** (-(continue_cost - 15)) + (math.e) ** ((aggression_factor - 1.5)))

            _SCARY = 0
            if continue_cost > 6:
                _SCARY = 0.1
            if continue_cost > 15:
                _SCARY = 0.20
            if continue_cost > 50:
                _SCARY = 0.35

            strength = max(0, strength - _SCARY)

            if strength >= pot_odds:  # nonnegative EV decision
                if strength > 0.5 and random.random() < strength:
                    my_action = temp_action
                else:
                    my_action = Action.CHECK_CALL

            else:  # negative EV
                my_action = Action.FOLD

        else:  # continue cost is 0
            if random.random() < strength:
                my_action = Action.FOLD
            else:
                my_action = Action.CHECK_CALL


        for i in range(len(legal_actions)):
            if repr(my_action) == repr(legal_actions[i]):
                my_action = legal_actions[i]

        return my_action


class ClassBotwithGWC2Model(Model):
    ''' Class Bot with GWC 2 Model
    '''

    def __init__(self):
        ''' Load pretrained model
        '''
        env = rlcard.make('river-of-blood-holdem')

        rule_agent = ClassBotwithGWC2Agent()
        self.rule_agents = [rule_agent for _ in range(env.num_players)]

    @property
    def agents(self):
        ''' Get a list of agents for each position in a the game

        Returns:
            agents (list): A list of agents

        Note: Each agent should be just like RL agent with step and eval_step
              functioning well.
        '''
        return self.rule_agents

    @property
    def use_raw(self):
        ''' Indicate whether use raw state and action

        Returns:
            use_raw (boolean): True if using raw state and action
        '''
        return True