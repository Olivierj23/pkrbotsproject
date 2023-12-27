# -*- coding: utf-8 -*-
"""Implement no limit texas holdem Round class"""
from enum import Enum

from rlcard.games.limitholdem import PlayerStatus


class Action(Enum):
    FOLD = 0
    CHECK_CALL = 1
    #CALL = 2
    # RAISE_3BB = 3
    RAISE_HALF_POT = 2
    RAISE_POT = 3
    # RAISE_2POT = 5
    ALL_IN = 4
    RAISE_5 = 5
    RAISE_15 = 6
    RAISE_50 = 7
    RAISE_100 = 8
    RAISE_200 = 9
    # SMALL_BLIND = 7
    # BIG_BLIND = 8


class NolimitholdemRound:
    """Round can call functions from other classes to keep the game running"""

    def __init__(self, num_players, init_raise_amount, dealer, np_random):
        """
        Initialize the round class

        Args:
            num_players (int): The number of players
            init_raise_amount (int): The min raise amount when every round starts
        """
        self.np_random = np_random
        self.game_pointer = None
        self.num_players = num_players
        self.init_raise_amount = init_raise_amount

        self.dealer = dealer

        # Count the number without raise
        # If every player agree to not raise, the round is over
        self.not_raise_num = 0

        # Count players that are not playing anymore (folded or all-in)
        self.not_playing_num = 0

        # Raised amount for each player
        self.raised = [0 for _ in range(self.num_players)]

    def start_new_round(self, game_pointer, raised=None):
        """
        Start a new bidding round

        Args:
            game_pointer (int): The game_pointer that indicates the next player
            raised (list): Initialize the chips for each player

        Note: For the first round of the game, we need to setup the big/small blind
        """
        self.game_pointer = game_pointer
        self.not_raise_num = 0
        if raised:
            self.raised = raised
        else:
            self.raised = [0 for _ in range(self.num_players)]

    def proceed_round(self, players, action):
        """
        Call functions from other classes to keep one round running

        Args:
            players (list): The list of players that play the game
            action (str/int): An legal action taken by the player

        Returns:
            (int): The game_pointer that indicates the next player
        """
        player = players[self.game_pointer]

        if action == Action.CHECK_CALL:
            diff = max(self.raised) - self.raised[self.game_pointer]
            self.raised[self.game_pointer] = max(self.raised)
            player.bet(chips=diff)
            self.not_raise_num += 1

        elif action == Action.ALL_IN:
            all_in_quantity = player.remained_chips
            self.raised[self.game_pointer] = all_in_quantity + self.raised[self.game_pointer]
            player.bet(chips=all_in_quantity)
            self.not_raise_num = 1

        elif action == Action.RAISE_POT:
            self.raised[self.game_pointer] += self.dealer.pot
            player.bet(chips=self.dealer.pot)
            self.not_raise_num = 1

        elif action == Action.RAISE_HALF_POT:
            quantity = int(self.dealer.pot / 2)
            self.raised[self.game_pointer] += quantity
            player.bet(chips=quantity)
            self.not_raise_num = 1

        elif action == Action.RAISE_5:
            quantity = 5
            self.raised[self.game_pointer] += quantity
            player.bet(chips=quantity)
            self.not_raise_num = 1

        elif action == Action.RAISE_15:
            quantity = 15
            self.raised[self.game_pointer] += quantity
            player.bet(chips=quantity)
            self.not_raise_num = 1

        elif action == Action.RAISE_50:
            quantity = 50
            self.raised[self.game_pointer] += quantity
            player.bet(chips=quantity)
            self.not_raise_num = 1

        elif action == Action.RAISE_100:
            quantity = 100
            self.raised[self.game_pointer] += quantity
            player.bet(chips=quantity)
            self.not_raise_num = 1

        elif action == Action.RAISE_200:
            quantity = 200
            self.raised[self.game_pointer] += quantity
            player.bet(chips=quantity)
            self.not_raise_num = 1



        elif action == Action.FOLD:
            player.status = PlayerStatus.FOLDED

        if player.remained_chips < 0:
            raise Exception("Player in negative stake")

        if player.remained_chips == 0 and player.status != PlayerStatus.FOLDED:
            player.status = PlayerStatus.ALLIN

        self.game_pointer = (self.game_pointer + 1) % self.num_players

        if player.status == PlayerStatus.ALLIN:
            self.not_playing_num += 1
            self.not_raise_num -= 1  # Because already counted in not_playing_num
        if player.status == PlayerStatus.FOLDED:
            self.not_playing_num += 1

        # Skip the folded players
        while players[self.game_pointer].status == PlayerStatus.FOLDED:
            self.game_pointer = (self.game_pointer + 1) % self.num_players

        return self.game_pointer

    def get_nolimit_legal_actions(self, players):
        """
        Obtain the legal actions for the current player

        Args:
            players (list): The players in the game

        Returns:
           (list):  A list of legal actions
        """

        full_actions = list(Action)

        # The player can always check or call
        player = players[self.game_pointer]

        diff = max(self.raised) - self.raised[self.game_pointer]
        # If the current player has no more chips after call, we cannot raise
        if diff > 0 and diff >= player.remained_chips:
            full_actions.remove(Action.RAISE_HALF_POT)
            full_actions.remove(Action.RAISE_POT)
            full_actions.remove(Action.ALL_IN)
            full_actions.remove(Action.RAISE_5)
            full_actions.remove(Action.RAISE_15)
            full_actions.remove(Action.RAISE_50)
            full_actions.remove(Action.RAISE_100)
            full_actions.remove(Action.RAISE_200)

        # Even if we can raise, we have to check remained chips
        else:
            if self.dealer.pot > player.remained_chips:
                full_actions.remove(Action.RAISE_POT)

            if int(self.dealer.pot / 2) > player.remained_chips:
                full_actions.remove(Action.RAISE_HALF_POT)

            if 5 > player.remained_chips:
                full_actions.remove(Action.RAISE_5)

            if 15 > player.remained_chips:
                full_actions.remove(Action.RAISE_15)

            if 50 > player.remained_chips:
                full_actions.remove(Action.RAISE_50)

            if 100 > player.remained_chips:
                full_actions.remove(Action.RAISE_100)

            if 200 > player.remained_chips:
                full_actions.remove(Action.RAISE_200)



            # Can't raise if the total raise amount is leq than the max raise amount of this round
            # If raise by pot, there is no such concern
            if Action.RAISE_HALF_POT in full_actions and \
                int(self.dealer.pot / 2) + self.raised[self.game_pointer] <= max(self.raised):
                full_actions.remove(Action.RAISE_HALF_POT)

            if Action.RAISE_5 in full_actions and \
                5 + self.raised[self.game_pointer] <= max(self.raised):
                full_actions.remove(Action.RAISE_5)

            if Action.RAISE_15 in full_actions and \
                15 + self.raised[self.game_pointer] <= max(self.raised):
                full_actions.remove(Action.RAISE_15)

            if Action.RAISE_50 in full_actions and \
                50 + self.raised[self.game_pointer] <= max(self.raised):
                full_actions.remove(Action.RAISE_50)

            if Action.RAISE_100 in full_actions and \
                100 + self.raised[self.game_pointer] <= max(self.raised):
                full_actions.remove(Action.RAISE_100)

            if Action.RAISE_200 in full_actions and \
                200 + self.raised[self.game_pointer] <= max(self.raised):
                full_actions.remove(Action.RAISE_200)


        return full_actions

    def is_over(self):
        """
        Check whether the round is over

        Returns:
            (boolean): True if the current round is over
        """
        if self.not_raise_num + self.not_playing_num >= self.num_players:
            return True
        return False
