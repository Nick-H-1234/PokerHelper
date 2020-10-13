import argparse


class Player:
    def __init__(self, name, stack):
        self.name = name.capitalize()
        self.stack = stack
        self.current_bet = 0
        self.folded = False
        self.all_in = False
        self.last_bettor = False
        self.big_blind = False
        self.big_blind_acted = False
        self.big_blind_checked = False
        self.first_action = False

    def __str__(self):
        return "%s : %s" % (self.name, self.stack)


class Pot:
    def __init__(self, players, value):
        self.players = players
        self.value = value


def check_win(players):
    active_players = 0
    for player in players:
        if not player.folded:
            active_players += 1
    return active_players == 1


def get_winner_by_folding(players):
    for player in players:
        if not player.folded:
            return player


def get_winner_by_showdown(players):
    while True:
        player_name = input("Please enter the winning player's name!")
        for player in players:
            if player.name == player_name:
                return player
        print("That name didn't match! It must be spelled the same as one of these: \n")
        for player in players:
            print(player.name)


def get_current_bets(players):
    result = 0
    for player in players:
        result += player.current_bet
    return result


def reset_players(players):
    for player in players:
        player.folded = False
        player.all_in = False
        player.last_bettor = False
        player.big_blind = False
        player.big_blind_acted = False
        player.big_blind_checked = False
        player.first_action = False


def play_hand(hand_players, big_blind, dealer):
    print("Starting a hand. Deal your cards now")
    # preflop
    pot = play_round(hand_players, dealer, 0, big_blind, preflop=True)
    if pot == 0:
        return
    print("Preflop round is over! Please deal the flop.")

    # flop
    pot = play_round(hand_players, dealer, pot)
    if pot == 0:
        return
    print("Flop round is over! Please deal the turn.")

    # turn
    pot = play_round(hand_players, dealer, pot)
    if pot == 0:
        return
    print("Turn round is over! Please deal the river.")

    # river
    play_round(hand_players, dealer, pot, river=True)
    return


def play_round(players, dealer, pot, bet=0, river=False, preflop=False):
    min_bet = 2 * bet
    playing_round = True
    # if pre-flop, post blinds and player left of big blind acts
    if preflop:
        current_player = players[(players.index(dealer) + 3) % len(players)]
        players[(players.index(dealer) + 2) % len(players)].big_blind = True
        # post small blind
        small_blind = players[(players.index(dealer) + 1) % len(players)]
        small_blind.current_bet = 0.5 * bet
        small_blind.stack -= 0.5 * bet
        print("%s posts a small blind of %s" % (small_blind.name, bet*0.5))
        # post big blind
        big_blind = players[(players.index(dealer) + 2) % len(players)]
        big_blind.last_bettor = True
        big_blind.current_bet = bet
        big_blind.stack -= bet
        print("%s posts a big blind of %s" % (big_blind.name, bet))

    # else, player left of dealer acts first
    else:
        current_player = players[(players.index(dealer) + 1) % len(players)]
        current_player.first_action = True

    # handle betting round
    while playing_round:

        # check for win by folding
        if check_win(players):
            playing_round = False
            break

        # if pre-flop, player is BB and hasn't acted yet, and all others only called or folded, he gets an action too
        if preflop and current_player.last_bettor and current_player.big_blind and not current_player.big_blind_acted:
            current_player.big_blind_acted = True

        # else if player was the last to bet and play returns to him, betting round is over
        elif current_player.last_bettor:
            playing_round = False
            break

        # skip folded or all-in players
        if current_player.all_in or current_player.folded:
            current_player = players[(players.index(current_player) + 1) % len(players)]
            continue

        # once checks are done, take player's action then move to the next player
        bet, min_bet = get_player_action(bet, min_bet, pot, players, current_player)

        # if player was first to act in post-flop round, then treat them as last bettor anyway if they check
        if current_player.first_action and not current_player.folded:
            current_player.last_bettor = True
        # else if they open fold, treat the next player along as 'first action'
        elif current_player.first_action and current_player.folded:
            players[(players.index(current_player) + 1) % len(players)].first_action = True

        # if it was just the Big Blind's 1st action and they checked, end betting round
        if current_player.last_bettor and current_player.big_blind and current_player.big_blind_checked:
            playing_round = False
            break
        current_player = players[(players.index(current_player) + 1) % len(players)]

    # after betting round, collect bets into pot and clean up
    for player in players:
        pot += player.current_bet
        player.current_bet = 0
        player.last_bettor = False
        player.big_blind_checked = False
        player.big_blind_acted = False

    print("Betting round is over. The pot is %s" % pot)

    # if only 1 player left, they win
    if check_win(players):
        winner = get_winner_by_folding(players)
        winner.stack += pot
        pot = 0

    # deal with winner at showdown
    if river:
        winner = get_winner_by_showdown(players)
        winner.stack += pot
        pot = 0

    return pot


def get_player_action(bet, min_bet, pot, players, current_player):
    valid_response = False
    while not valid_response:
        response = input("\n%s, it's your turn to bet. \n"
                         "There is %s in the pot, and %s chips have been bet by other players \n"
                         "Current bet is %s, and you have bet %s so far this round. \n"
                         "You have %s chips left in your stack. \n"
                         "Would you like to (R)aise, %s, (F)old, or go (A)ll-in?\n" %
                         (current_player.name, "nothing" if pot == 0 else pot, get_current_bets(players), bet,
                          current_player.current_bet, current_player.stack,
                          "(C)heck" if bet == current_player.current_bet else "(C)all"))
        # raise
        if response.lower() == "r":
            valid_action = False
            while not valid_action:
                if current_player.current_bet != 0:
                    print("You have already bet %s chips." % current_player.current_bet)
                try:
                    player_bet = float(input("Enter the total of your raise, or enter 0 to cancel: "))
                except Exception:
                    print("that wasn't a valid bet!")
                    break
                # cancel
                if player_bet == 0:
                    break

                # legal bet
                elif (player_bet >= min_bet) and (player_bet < (current_player.stack + current_player.current_bet)):
                    current_player.stack = current_player.stack - (player_bet - current_player.current_bet)
                    current_player.current_bet = player_bet
                    min_bet = 2 * player_bet - bet
                    bet = player_bet

                    for player in players:
                        player.last_bettor = False
                    current_player.last_bettor = True
                    print("Your bet is now %s chips!" % current_player.current_bet)
                    valid_action = True
                    valid_response = True

                # all in
                elif player_bet == current_player.stack:
                    current_player.current_bet = player_bet
                    current_player.stack = 0
                    bet = player_bet
                    current_player.all_in = True
                    print("%s is now all in! They've bet %s chips." % (current_player.name, current_player.current_bet))
                    valid_action = True
                    valid_response = True

                # invalid bet
                if not valid_action:
                    print("That's not a valid raise! "
                          "You have %s chips and need to bet at least a total of %s." % (current_player.stack, min_bet))
                    print("\n")

        # check / call
        elif response.lower() == "c":
            if bet == current_player.current_bet:
                print("You have checked.")
            elif current_player.stack + current_player.current_bet > bet:
                print("You called for %s chips" % bet)
                current_player.stack = current_player.stack - (bet - current_player.current_bet)
                current_player.current_bet = bet
            else:
                print("You've called and gone all in!")
                current_player.current_bet = current_player.current_bet + current_player.stack
                current_player.stack = 0
                current_player.all_in = True
            if current_player.big_blind:
                current_player.big_blind_checked = True
            valid_response = True

        # fold
        elif response.lower() == "f":
            current_player.folded = True
            valid_response = True

        # all in
        elif response.lower() == "a":
            # all in for greater than current bet
            if current_player.current_bet + current_player.stack > bet:
                bet = current_player.current_bet + current_player.stack

            current_player.current_bet = current_player.stack + current_player.current_bet
            current_player.stack = 0
            current_player.all_in = True
            print("%s is now all in! They've bet %s chips." % (current_player.name, current_player.current_bet))
            valid_response = True

    return bet, min_bet


def main():
    parser = argparse.ArgumentParser(usage="")
    parser.add_argument("-n", "--names", nargs='+', help="The names of the players.", required=True)
    parser.add_argument("-s", "--stack", type=float, help="The stack size of each player at buy-in.", required=True)
    parser.add_argument("-b", "--blind", type=float, help="The big blind. Small blind is half this.", required=True)
    args = parser.parse_args()
    player_names = args.names
    stack_size = args.stack
    big_blind = args.blind

    players = []
    for name in player_names:
        players.append(Player(name, stack_size))

    for player in players:
        print(player)
    print("\n")

    playing_game = True
    game_players = players.copy()
    dealer = game_players[0]
    while playing_game:
        play_hand(game_players, big_blind, dealer)
        reset_players(game_players)
        for player in players:
            if player.stack == stack_size * len(players):
                playing_game = False
                print("Game over! %s Wins!" % player.name)
            elif player.stack == 0:
                game_players.remove(player)
                print("%s has busted!" % player.name)
        if not playing_game:
            break
        print("Hand over! The standings so far:")
        for player in players:
            print(player)
        dealer = game_players[(game_players.index(dealer) - 1) % len(game_players)]


if __name__ == "__main__":
    main()
