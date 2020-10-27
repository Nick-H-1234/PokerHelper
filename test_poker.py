from unittest import TestCase
from unittest.mock import patch
from poker import Player, Pot, get_player_action

player1 = Player("Player one", 0)
player2 = Player("Player two", 0)
player3 = Player("Player three", 0)

players = [player1, player2, player3]


class Test(TestCase):
    @patch('poker.input', return_value='c')
    def test_get_player_action(self, input):
        bet = 10
        min_bet = 5
        pots = [Pot(players, 10)]
        current_player = player1
        self.assertEqual(get_player_action(bet, min_bet, pots, players, current_player), (10, 5))
