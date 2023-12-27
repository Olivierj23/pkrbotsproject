'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random
import eval7
import math


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.
        Arguments:
        Nothing.
        Returns:
        Nothing.
        '''
        self.total_score = 0

    def calc_strength(self, hole, iters, community = []):
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


    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.
        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.
        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind





    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.
        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.
        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed

        self.total_score += my_delta


    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.
        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.
        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        round_num = game_state.round_num
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        net_upper_raise_bound = round_state.raise_bounds()
        stacks = [my_stack, opp_stack] #keep track of our stacks
        big_blind = bool(active)  # True if you are the big blind

        my_action = None
        min_raise, max_raise = round_state.raise_bounds()
        pot_total = my_contribution + opp_contribution

        # running monte carlo simulation when we have community cards vs when we don't

        _MONTE_CARLO_ITERS = 100

        if street < 3:
            strength = self.calc_strength(my_cards, _MONTE_CARLO_ITERS)
        else:
            strength = self.calc_strength(my_cards, _MONTE_CARLO_ITERS, board_cards)



        MDF = pot_total/(pot_total + continue_cost)
        pot_odds = continue_cost/(pot_total + continue_cost)
        rounds_left = NUM_ROUNDS - round_num

        # Calculations for the Kelly Criterion where p is probailtity of winning/ q is probability of losing/ b is betting ratio
        p = strength
        q = 1-p
        b =(pot_total+continue_cost)/(my_contribution+continue_cost)



        # raise logic with Kelly Criterion
        if street <3: #preflop
                raise_amount = int(my_pip + continue_cost + (p-q/b)*(pot_total))

        else: #postflop
                raise_amount = int(my_pip + continue_cost + (p-q/b)*(pot_total))

        # # ensure raises are legal
        raise_amount = max([min_raise, raise_amount]) #getting the max of the min raise and the raise amount
        raise_amount = min([max_raise, raise_amount]) #getting the min of the max raise and the raise amount
        # # we want to do this so that we don't raise more than the max raise or less than the min raise


        if (RaiseAction in legal_actions and (raise_amount <= my_stack)):
            temp_action = RaiseAction(raise_amount)
        elif (CallAction in legal_actions and (continue_cost <= my_stack)):
            temp_action = CallAction()
        elif CheckAction in legal_actions:
            temp_action = CheckAction()
        else:
            temp_action = FoldAction()



        if continue_cost > 0:

            _SCARY = 0
            if continue_cost > 6:
                _SCARY = 0.1
            if continue_cost > 15:
                _SCARY = 0.20
            if continue_cost > 50:
                _SCARY = 0.35

            strength = max(0, strength - _SCARY)


            if strength >= pot_odds: # nonnegative EV decision with MDF consideration
                if strength > 0.5 and random.random() < strength:
                    my_action = temp_action
                else:
                    my_action = CallAction()

            else: #negative EV
                my_action = FoldAction()

        else: # continue cost is 0
            if random.random() < strength:
                my_action = temp_action
            else:
                my_action = CheckAction()

        # Guaranteed win condition ( when we can secure our win just by folding)
        if self.total_score > 2 + rounds_left//2 + 2*(rounds_left-rounds_left//2):
            if FoldAction in legal_actions:
                my_action = FoldAction()
            else:
                my_action = CheckAction()


        # printing out key information we want to see in the player logs
        print(round_num)
        print(street)
        print(pot_odds, MDF)
        print((self.total_score, 2 + rounds_left // 2 + 2 * (rounds_left - rounds_left // 2)))
        print(legal_actions)



        return my_action





if __name__ == '__main__':
    run_bot(Player(), parse_args())

