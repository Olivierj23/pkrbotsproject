'''
Simple example pokerbot, written in Python.
'''
import eval7
import random
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot


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

        self.good_hand = False
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

    def allocate_cards(self, my_cards):
        ranks = {}



        for card in my_cards:
            card_rank  = card[0]
            card_suit = card[1]


            if card_rank in ranks:
                ranks[card_rank].append(card)
            else:
                ranks[card_rank] = [card]

        pairs = [] #keeps track of the pairs that we have 
        singles = [] #other 

        for rank in ranks:
            cards = ranks[rank]

            if len(cards) == 1: #single card, can't be in a pair
                singles.append(cards[0])
            
            else: #len(cards) == 2: #a single pair can be made here, add them all
                pairs += cards
                pairs.append(cards[0])



        if len(pairs) > 0: #we found a pair! update our state to say that this is a strong round
            self.strong_hole = True
        
        allocation = pairs + singles 
        pass

    

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

        self.allocate_cards(my_cards) #allocate our cards to our board allocations

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

        self.good_hand = False
        self.strong_hole = False #reset our strong hole flag
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
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        net_upper_raise_bound = round_state.raise_bounds()
        stacks = [my_stack, opp_stack] #keep track of our stacks

        combined_cards = my_cards + board_cards
        eval7_combined_cards = [eval7.Card(s) for s in combined_cards]
        eval7_my_cards = [eval7.Card(s) for s in my_cards]

        # calculate min/max raise/cost
        min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
        min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
        max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        if eval7.handtype(eval7.evaluate(eval7_combined_cards)) in ["Trips", "Quads", "Straight", "Flush", "Straight Flush", "Full House", "Royal Flush"]:
            print(round_num)
            print("I have a {}".format(eval7.handtype(eval7.evaluate(eval7_combined_cards))))
            self.good_hand = True

        pot = my_contribution + opp_contribution

        MDF = pot/(pot+continue_cost)

        net_cost = 0
        my_action = None

        if (RaiseAction in legal_actions) and (self.good_hand or self.strong_hole): #only consider raising if the hand we have is strong
            min_raise, max_raise = round_state.raise_bounds()
            max_cost = max_raise - my_pip

            if max_cost <= my_stack - net_cost: #make sure the max_cost is something we can afford! Must have at least this much left after our other costs
                my_action = RaiseAction(max_raise)
                net_cost += max_cost
            
            elif CallAction in legal_actions: # check-call
                my_action = CallAction()
                net_cost += continue_cost

            else:
                my_action = CheckAction()
        elif CheckAction in legal_actions: #if we can call, do so
            my_action = CheckAction()

        else:
            if street > 0:
                my_action = random.choices([CallAction(), FoldAction()], weights=(MDF, 1-MDF))[0]
                if my_action == FoldAction():
                    net_cost += 0 #add the cost of the continue to our net cost
                elif my_action == FoldAction():
                    net_cost += continue_cost

            elif CallAction in legal_actions:
                my_action = CallAction()
                net_cost += continue_cost


        return my_action



        


if __name__ == '__main__':
    run_bot(Player(), parse_args())
