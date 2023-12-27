import pickle

#FIXME: package local import in zip file
import xgboost as xgb
import numpy as np
import eval7

from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

action_from_encoding = {0:FoldAction,1:CallAction, 2:CheckAction, 3: RaiseAction}
MAX_CARDS = 15
def card_strs2vec(cards:list[str]):
    card_encodings = np.zeros((4+13)*MAX_CARDS)
    
    for card_idx, card_str in enumerate(cards):
        card = eval7.Card(card_str)
        #print("card.rank", card.rank, "card.suit", card.suit)
        offset = (4+13)*card_idx

        card_encodings[offset + card.suit] = 1
        card_encodings[offset + 4 + card.rank] = 1
    return card_encodings

MODEL_FNAME = "xgb_model.pkl"


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
        
        self.xgbc_model = pickle.load(open(MODEL_FNAME, "rb"))

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
        # VARIABLE INIT
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # int representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        
        min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
        min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
        max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        # ML LOGIC
        card_encoding = card_strs2vec(my_cards+board_cards)
        pot_size = my_contribution+opp_contribution

        gamestate_vector = [card_encoding+[pot_size]]
        
        raise_amount = 50 # FIXME: intelligently determine raise amount
        raise_amount = max(min_raise, raise_amount)
        raise_amount = min(max_raise, raise_amount)

        xgb_action = action_from_encoding[self.xgbc_model.predict(gamestate_vector)[0]]
        if xgb_action in legal_actions:
            if xgb_action == RaiseAction:
                return RaiseAction(raise_amount)
            else:
                return xgb_action()
        else:
            print("XGB Returned Invalid Action")
            if CheckAction in legal_actions:  # check-call
                return CheckAction()
            return CallAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())
