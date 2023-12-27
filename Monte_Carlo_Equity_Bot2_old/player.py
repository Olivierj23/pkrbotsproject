'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
import eval7
import copy
import random


def allocate_cards(player_cards=[], board_cards=[]):
    my_ranks = {}
    my_suits = {}
    combined_hand=player_cards + board_cards
    print(combined_hand)
    for card in combined_hand:
        card_rank = card[0]
        card_suit = card[1]
        if card_rank in my_ranks:
            my_ranks[card_rank].append(card)

        else:
            my_ranks[card_rank] = [card]

        if card_suit in my_suits:
            my_suits[card_suit].append(card)
        else:
            my_suits[card_suit] = [card]

    return my_ranks, my_suits

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
        self.strong_hole = False
        self.One_Pair = False
        self.Two_Pairs = False
        self.Three_of_A_Kind = False
        self.Straight = False
        self.Flush = False
        self.Full_House = False
        self.Four_of_a_Kind = False
        self.Straight_Flush = False
        self.Royal_Flush = False
        self.Ace = False

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
        street = previous_state.street  # int of street representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed


        self.total_score += my_delta

        self.strong_hole = False
        self.One_Pair = False
        self.Two_Pairs = False
        self.Three_of_A_Kind = False
        self.Straight = False
        self.Flush = False
        self.Full_House = False
        self.Four_of_a_Kind = False
        self.Straight_Flush = False
        self.Royal_Flush = False
        self.Ace = False



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
        street = round_state.street  # int representing pre-flop, flop, turn, or river respectively
        round_num = game_state.round_num
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot

        pot = my_contribution + opp_contribution

        MDF = pot/(pot + continue_cost)

        net_cost = 0
        my_action = None

        #asseemble cards to enter into eval7
        combined_cards = my_cards+board_cards
        eval7_my_hole = [eval7.Card(s) for s in my_cards]
        eval7_board_cards = [eval7.Card(s) for s in board_cards]

        #determine villain range for equity calculator
        #villain_range =eval7.HandRange("22+") #eval7.HandRange("22+,32+,42+,52+,62+,72+,82+,92+,T2+,J2+,Q2+,K2+,A2+")

        #calculate min/max raise/cost
        min_raise, max_raise = round_state.raise_bounds() # the smallest and largest numbers of chips for a legal bet/raise
        min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
        max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        #calculate pot equity/odds depending on call or raise
        pot_equity_with_call = continue_cost/(my_contribution + opp_contribution + continue_cost)
        pot_equity_with_raise = min_cost/(my_contribution + opp_contribution + min_cost)

        #conditional to calculate implied equity depending on street
        if street <= 5:
            implied_equity = continue_cost/(my_contribution + opp_contribution + continue_cost + 2*continue_cost)
        else:
            if round_state.deck[:street][-1][1] in ['h', 'd']:
                implied_equity = continue_cost/(my_contribution + opp_contribution + continue_cost + 2*continue_cost)
            elif round_state.deck[:street][-1][1] in ['c', 's']:
                implied_equity = continue_cost / (my_contribution + opp_contribution + continue_cost)

        #calculate hand equity
        #hand_equity = eval7.py_hand_vs_range_monte_carlo(eval7_my_hole, villain_range, eval7_board_cards, 1000)

        if street <= 5:
            hand_equity = calc_strength(my_cards, board_cards, 5-street, 100)
        elif round_state.deck[:street][-1][1] in ['h', 'd']:
            hand_equity = calc_strength(my_cards, board_cards, 1, 100)
        elif round_state.deck[:street][-1][1] in ['c', 's']:
            hand_equity = calc_strength(my_cards, board_cards, 0, 100)

        rounds_left = 1000 - round_num

        #some print statements for analysis
        print(round_num)
        print(street)
        print((self.total_score, rounds_left//2 + 2*(rounds_left-rounds_left//2)))
        print((hand_equity, pot_equity_with_raise, pot_equity_with_call, implied_equity))


        if self.total_score > rounds_left//2 + 2*(rounds_left-rounds_left//2):
            if FoldAction in legal_actions:
                my_action = FoldAction()
                print("I fold")
            else:
                my_action = CheckAction()
                print("I check")


        elif hand_equity >= pot_equity_with_raise:  # and (street >= 3):
            if max_cost <= my_stack - net_cost and (RaiseAction in legal_actions):
                my_action = RaiseAction(max_raise)
                net_cost += max_cost
                print("I raise!")


            elif CallAction in legal_actions:
                my_action = CallAction()
                net_cost += continue_cost
                print("I call!")

            else:
                my_action = CheckAction()
                print("I check!")

        elif (hand_equity >= pot_equity_with_call) and (street >= 3):

            if CallAction in legal_actions:
                my_action = CallAction()
                net_cost += continue_cost
                print("I call!")

            else:
                my_action = CheckAction()
                print("I check!")

        elif hand_equity >= implied_equity:

            if CheckAction in legal_actions:
                my_action = CheckAction()
                print("I check")

            elif FoldAction in legal_actions:
                my_action = random.choices([FoldAction(), CallAction()], weights=(1 - MDF, MDF))[0]
                if my_action == FoldAction():
                    print("I fold!")
                elif my_action == CallAction():
                    print("I call!")
                    net_cost += continue_cost

            elif CallAction in legal_actions:
                my_action = CallAction()
                net_cost += continue_cost
                print("I call")

        elif hand_equity < implied_equity:
            if CheckAction in legal_actions:
                my_action = CheckAction()
                print("I check")
            else:
                my_action = FoldAction()
                print("I fold")

        return my_action

if __name__ == '__main__':
    run_bot(Player(), parse_args())