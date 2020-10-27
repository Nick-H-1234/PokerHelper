import argparse


class Player:
    def __init__(self, name, stack):
        self.name = name.capitalize()
        self.stack = stack
        self.current_bet = 0
        self.hand_total_invested = 0
        self.folded = False
        self.all_in = False
        self.last_bettor = False
        self.big_blind = False
        self.big_blind_acted = False
        self.big_blind_checked = False
        self.first_action = False

    def __str__(self):
        return "%s : %s" % (self.name, self.stack)

    # TODO make a "make bet" method for DRY reasons
    def make_bet(self, bet_total):
        pass


class Pot:
    def __init__(self, players, value):
        self.players = players.copy()
        self.value = value

    def __str__(self):
        return "Players: %s \n Value: %s" % (self.players, self.value)


def get_next_player(players, player, postions_number=1):
    return players[(players.index(player) + postions_number) % len(players)]


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
        player.current_bet = 0
        player.hand_total_invested = 0


def skip_to_showdown(players):
    count = 0
    for player in players:
        if player.folded or player.all_in:
            count += 1
    return count >= len(players) - 1


def play_hand(hand_players, big_blind, dealer):
    print("Starting a hand. Deal your cards now")
    # preflop
    main_pot = Pot(hand_players, 0)
    pots = [main_pot]
    pots = play_round(hand_players, dealer, pots, big_blind, preflop=True)
    if pots[0].value == 0:
        return
    print("Preflop round is over! Please deal the flop.")

    # flop
    pots = play_round(hand_players, dealer, pots)
    if pots[0].value == 0:
        return
    print("Flop round is over! Please deal the turn.")

    # turn
    pots = play_round(hand_players, dealer, pots)
    if pots[0].value == 0:
        return
    print("Turn round is over! Please deal the river.")

    # river
    play_round(hand_players, dealer, pots, river=True)
    return


def play_round(players, dealer, pots, bet=0, river=False, preflop=False):
    min_bet = 2 * bet
    playing_round = True
    # if pre-flop, post blinds and player left of big blind acts
    if preflop:
        current_player = get_next_player(players, dealer, 3)
        # post small blind
        small_blind = get_next_player(players, dealer)
        small_blind.current_bet = 0.5 * bet
        small_blind.stack -= 0.5 * bet
        small_blind.hand_total_invested += 0.5 * bet
        print("%s posts a small blind of %s" % (small_blind.name, bet*0.5))
        # post big blind
        big_blind = get_next_player(players, dealer, 2)
        big_blind.big_blind = True
        big_blind.last_bettor = True
        big_blind.current_bet = bet
        big_blind.stack -= bet
        big_blind.hand_total_invested += bet
        print("%s posts a big blind of %s" % (big_blind.name, bet))

    # else, player left of dealer acts first
    else:
        current_player = get_next_player(players, dealer)
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
            current_player = get_next_player(players, current_player)
            continue

        # once checks are done, take player's action then move to the next player
        bet, min_bet = get_player_action(bet, min_bet, pots, players, current_player)

        # if player was first to act in post-flop round, then treat them as last bettor anyway if they check
        if current_player.first_action and not current_player.folded:
            current_player.last_bettor = True
        # else if they open fold, treat the next player along as 'first action'
        elif current_player.first_action and current_player.folded:
            get_next_player(players, current_player).first_action = True

        # if it was just the Big Blind's 1st action and they checked, end betting round
        if current_player.last_bettor and current_player.big_blind and current_player.big_blind_checked:
            playing_round = False
            break
        current_player = get_next_player(players, current_player)

    # after betting round, manage side pots fist
    # If someone is all in, there's a potential for a side pot to be created
    all_in_players = [player for player in players if player.all_in]
    unique_all_in_amounts = list(set([p.hand_total_invested for p in all_in_players]))
    unique_all_in_amounts.sort()
    if len(all_in_players):
        # if there are any players who have invested more than the lowest all-in player, we need a side pot
        # (the all-in player's bet goes in main pot with everyone else's)
        # for each player or players who are all-in for x amount, with total bet higher, new side pot is needed
        for i in unique_all_in_amounts:
            eligible_players = [player for player in players if player.hand_total_invested > i]
            eligible_player_investments = [x.hand_total_invested for x in eligible_players]
            if len(eligible_players) > 1:
                # if multiple players, make a side pot
                pots.append(Pot(eligible_players, ((min(eligible_player_investments) -
                                                    i) * len(eligible_players))))
            if len(eligible_players) == 1:
                # if only 1 player in a potential side pot, just refund him his chips over the last (lower) all in
                eligible_players[0].stack += (eligible_player_investments[0] - i)

        # check for folded players and make them unable to win any pots
        for player in players:
            if player.folded:
                for pot in pots:
                    if player in pot.players:
                        pot.players.remove(player)

        # if a side pot only has 1 player eligible for it (i.e. all others folded) then that player wins that pot
        for i in range(len(pots)):
            if len(pots[i].players) == 1:
                pots[i].players[0].stack += pots[i].value
                pots.remove(pots[i])

        # collect all bets of value equal to the minimum all-in into main pot and set "current bet" to 0 for everyone
        # unless they folded for less, in which case add as much as they bet
        for player in players:
            pots[0].value += min([min(unique_all_in_amounts), player.current_bet])
            player.current_bet = 0

    else:
        # no all-ins, just put all bets in main pot and continue
        for player in players:
            pots[0].value += player.current_bet
            player.current_bet = 0
            player.last_bettor = False
            player.big_blind_checked = False
            player.big_blind_acted = False

    print("Betting round is over. The main pot is %s" % pots[0].value)
    if len(pots) > 1:
        print("Side pot standings are: ")
        for i in range(1, len(pots)):
            print("Side pot %s: " % i, pots[i])

    # if only 1 player left in a pot, they win that pot
    for pot in pots:
        if check_win(pot.players):
            winner = get_winner_by_folding(pot.players)
            winner.stack += pot.value
            pot.value = 0

    # deal with winner at showdown if there's just the main pot
    # if river and len(pots) == 1:
    #     winner = get_winner_by_showdown(players)
    #     winner.stack += pots[0].value
    #     pots[0].value = 0

    # if we have side pots at the showdown, handle them here
    if river:
        for i in range(len(pots)):
            print("Dealing with %s" % ("the main pot" if i == 0 else "side pot %s" % (str(i-1))))
            winner = get_winner_by_showdown(pots[i].players)
            winner.stack += pots[i].value
            pots[i].value = 0
    return pots


def get_player_action(bet, min_bet, pots, players, current_player):
    valid_response = False
    side_pot_values = 0
    for i in range(1, len(pots)):
        side_pot_values += pots[i].value
    while not valid_response:
        response = input("\n%s, it's your turn to bet. \n"
                         "There is %s in the main pot, and %s \n"
                         "%s chips have been bet by other players \n"
                         "Current bet is %s, and you have bet %s so far this round. \n"
                         "You have %s chips left in your stack. \n"
                         "Would you like to (R)aise, %s, (F)old, or go (A)ll-in?\n" %
                         (current_player.name,
                          "nothing" if pots[0].value == 0 else pots[0].value,
                          "there are no side pots" if len(pots) == 1 else "the side pots are worth %s" % side_pot_values,
                          get_current_bets(players),
                          bet, current_player.current_bet, current_player.stack,
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
                    current_player.hand_total_invested += player_bet
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
                    current_player.hand_total_invested += player_bet
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
                current_player.hand_total_invested += (bet - current_player.current_bet)

            else:
                # all in call
                print("You've called and gone all in!")
                current_player.current_bet = current_player.current_bet + current_player.stack
                current_player.hand_total_invested += current_player.stack
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
                current_player.last_bettor = True

            current_player.current_bet = current_player.stack + current_player.current_bet
            current_player.hand_total_invested += current_player.stack
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

    total_chips = len(players) * stack_size

    for player in players:
        print(player)
    print("\n")

    playing_game = True
    game_players = players.copy()
    dealer = game_players[0]
    while playing_game:
        play_hand(game_players, big_blind, dealer)
        print("Hand over! The standings so far:")
        for player in players:
            print(player)
        dealer_busted = False
        for player in game_players:
            if player.stack == total_chips:
                playing_game = False
                print("Game over! %s Wins!" % player.name)
                break
            elif player.stack == 0:
                if dealer is player:
                    dealer = get_next_player(game_players, dealer)
                    print("dealer busted")
                    dealer_busted = True
                game_players.remove(player)
                print("%s has busted!" % player.name)
        if not dealer_busted:
            dealer = get_next_player(game_players, dealer)

        reset_players(game_players)


if __name__ == "__main__":
    main()
