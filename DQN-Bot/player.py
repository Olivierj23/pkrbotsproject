'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import numpy as np
import rlcard
import torch
from rlcard.games.riverofbloodholdem.round import Action



def closest_value(input_list, input_value):
    arr = np.asarray(input_list)
    i = (np.abs(arr - input_value)).argmin()
    return arr[i]

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
        self.action_recorder = []
        model_path = "rlcard/games/nolimitholdem/experiments/river_of_blood_holdem_dqn_result_against_Random_Agent/model.pth"
        self.agent = torch.load(model_path)
        self.total_score = 0



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

        self.action_recorder = []




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

    def state(self, legal_actions, public_cards, hand, round_state, active):
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1 - active]  # the number of chips your opponent has remaining
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        
        state = {}
        #public cards
        state['public_cards'] = [s[1].upper() + s[0] for s in public_cards]
        #hand
        state['hand'] = [s[1].upper() + s[0] for s in hand]
        #my_chips
        state['my_chips'] = my_contribution
        #all_chips
        state['all_chips'] = [opp_contribution, my_contribution]
        #state
        state['legal_actions'] = legal_actions

        return state
        
        



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
        pot = my_contribution + opp_contribution
        min_raise, max_raise = round_state.raise_bounds()
        

        if my_pip != opp_pip:
            opp_raise = closest_value([pot, int(pot / 2), 5, 15, 50, 100, 200, 400], abs(opp_pip - my_pip))
            if opp_raise == int(pot / 2):
                self.action_recorder.append((0, Action(2)))
            elif opp_raise == pot:
                self.action_recorder.append((0, Action(3)))
            elif opp_raise == 5:
                self.action_recorder.append((0, Action(4)))
            elif opp_raise == 15:
                self.action_recorder.append((0, Action(5)))
            elif opp_raise == 50:
                self.action_recorder.append((0, Action(6)))
            elif opp_raise == 100:
                self.action_recorder.append((0, Action(7)))
            elif opp_raise == 200:
                self.action_recorder.append((0, Action(8)))

        else:
            self.action_recorder.append((0, Action(1)))







        diff = continue_cost
        full_actions = list(Action)
        
        if diff > 0 and diff >= my_stack:
            full_actions.remove(Action.RAISE_HALF_POT)
            full_actions.remove(Action.RAISE_POT)
            full_actions.remove(Action.ALL_IN)
            full_actions.remove(Action.RAISE_5)
            full_actions.remove(Action.RAISE_15)
            full_actions.remove(Action.RAISE_50)
            full_actions.remove(Action.RAISE_100)
            full_actions.remove(Action.RAISE_200)
        
        else:
            if pot > my_stack or pot > max_raise or pot < min_raise:
                full_actions.remove(Action.RAISE_POT)
            if int(pot / 2) > my_stack or int(pot / 2) > max_raise or int(pot / 2) < min_raise:
                full_actions.remove(Action.RAISE_HALF_POT)
            if 5 > my_stack or 5 > max_raise or 5 < min_raise:
                full_actions.remove(Action.RAISE_5)
            if 15 > my_stack or 15 > max_raise or 15 < min_raise:
                full_actions.remove(Action.RAISE_15)
            if 50 > my_stack or 50 > max_raise or 50 < min_raise:
                full_actions.remove(Action.RAISE_50)
            if 100 > my_stack or 100 > max_raise or 100 < min_raise:
                full_actions.remove(Action.RAISE_100)
            if 200 > my_stack or 200 > max_raise or 200 < min_raise:
                full_actions.remove(Action.RAISE_200)


        pre_extracted_state = self.state(full_actions, board_cards, my_cards, round_state, active)
        env = rlcard.make('river-of-blood-holdem')
        env.action_recorder = self.action_recorder
        extracted_state = env._extract_state(pre_extracted_state)


        my_action_id = self.agent.step(extracted_state)
        action_translator = [FoldAction(), CheckAction(), RaiseAction(int(pot / 2) + my_contribution), RaiseAction(pot + my_contribution), RaiseAction(5 + my_contribution), RaiseAction(15 + my_contribution), RaiseAction(50 + my_contribution), RaiseAction(100 + my_contribution), RaiseAction(200 + my_contribution), RaiseAction(max_raise)]
        my_action = action_translator[my_action_id]

        print("Hello")

        # Guaranteed win condition
        rounds_left = NUM_ROUNDS - round_num
        if self.total_score > 2 + rounds_left // 2 + 2 * (rounds_left - rounds_left // 2):
            if FoldAction in legal_actions:
                my_action = FoldAction()
            else:
                my_action = CheckAction()

        return my_action



        


if __name__ == '__main__':
    run_bot(Player(), parse_args())
