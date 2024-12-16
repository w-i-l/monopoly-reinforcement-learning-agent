from game.game_state import GameState
from models.chance_card import ChanceCard
from random import shuffle
from typing import List

class ChanceManager:
    def __init__(self):
        self.chance_cards = self.__load_cards()
        self.__shuffle_cards()


    def __shuffle_cards(self):
        self.__shuffled_cards = list(range(len(self.chance_cards)))
        shuffle(self.__shuffled_cards)


    def draw_card(self, game_state: GameState, player) -> ChanceCard:
        if len(self.__shuffled_cards) == 0:
            self.__shuffle_cards()

        card_id = self.__shuffled_cards.pop(0)
        card = self.chance_cards[card_id]

        return ChanceCard(
            id=card[0],
            description=card[1],
            action=card[2],
            args=(game_state, player, *card[3])
        )


    def __move_player_to_nearest_utility(self, game_state: GameState, player):
        utilities = game_state.board.get_utilities()
        player_position = game_state.player_positions[player]

        # Find the nearest utility
        nearest_utility = None
        min_distance = 100
        for utility in utilities:
            distance = abs(utility.id - player_position)
            if distance < min_distance:
                min_distance = distance
                nearest_utility = utility

        game_state.move_player_to_property(player, nearest_utility)

        # Pay rent or buy the utility
        if utility in game_state.is_owned and \
            not utility in game_state.properties[player] and\
            not utility in game_state.mortgaged_properties:
            game_state.pay_rent(player, utility, utility_factor_multiplier=10)
        else:
            if player.should_buy_property(game_state, utility):
                try:
                    game_state.buy_property(player, utility)
                except Exception as e:
                    print("Error", e)


    def __pay_tax(self, game_state: GameState, player, tax: int):
        game_state.pay_tax(player, tax)


    def __pay_tax_for_buildings(self, game_state: GameState, player):
        tax = 0

        houses_count = 0
        for property_group in game_state.houses:
            owner = game_state.houses[property_group][1]
            if owner == player:
                no_of_houses = game_state.houses[property_group][0]
                no_of_properties = len(game_state.board.get_properties_by_group(property_group))
                houses_count += no_of_houses * no_of_properties

        hotels_count = 0
        for property_group in game_state.hotels:
            owner = game_state.hotels[property_group][1]
            if owner == player:
                no_of_properties = len(game_state.board.get_properties_by_group(property_group))
                hotels_count += no_of_properties

        tax = houses_count * 25 + hotels_count * 100
        game_state.pay_tax(player, tax)


    def __move_player_to_start(self, game_state: GameState, player):
        start_tile = game_state.board.get_tile_by_name("Start")
        game_state.move_player_to_property(player, start_tile)

    
    def __receive_income(self, game_state: GameState, player, amount: int):
        game_state.receive_income(player, amount)


    def __move_player_to_nearest_railway(self, game_state: GameState, player, railway_factor_multiplier: int = None):
        railways = game_state.board.get_railways()
        player_position = game_state.player_positions[player]

        # Find the nearest railway
        nearest_railway = None
        min_distance = 100
        for railway in railways:
            distance = abs(railway.id - player_position)
            if distance < min_distance:
                min_distance = distance
                nearest_railway = railway

        game_state.move_player_to_property(player, nearest_railway)

        # Pay rent or buy the railway
        if railway in game_state.is_owned and \
            not railway in game_state.properties[player] and\
            not railway in game_state.mortgaged_properties:
            game_state.pay_rent(player, railway, railway_factor_multiplier)
        else:
            if player.should_buy_property(game_state, railway):
                try:
                    game_state.buy_property(player, railway)
                except Exception as e:
                    print("Error", e)
                

    def __move_player_to_jail(self, game_state: GameState, player):
        game_state.sent_player_to_jail(player)

    
    def __move_player_backwards(self, game_state: GameState, player, steps: int):
        game_state.move_player_backwards(player, steps)

        current_player_position = game_state.player_positions[player]
        tile = game_state.board.tiles[current_player_position]
        if tile in game_state.is_owned and \
            not tile in game_state.properties[player] and\
            not tile in game_state.mortgaged_properties:
            game_state.pay_rent(player, tile)


    def __move_player_to_property(self, game_state: GameState, player, property_name: str):
        property_tile = game_state.board.get_tile_by_name(property_name)
        if property_tile is None:
            print(game_state.board.tiles)
            exit(0)
        game_state.move_player_to_property(player, property_tile)

        if property_tile in game_state.is_owned and \
            not property_tile in game_state.properties[player] and\
            not property_tile in game_state.mortgaged_properties:
            game_state.pay_rent(player, property_tile)
        else:
            if player.should_buy_property(game_state, property_tile):
                try:
                    game_state.buy_property(player, property_tile)
                except Exception as e:
                    print("Error", e)


    def __receive_get_out_of_jail_card(self, game_state: GameState, player):
        game_state.receive_get_out_of_jail_card(player)
        
    
    def __pay_players(self, game_state: GameState, player, amount: int):
        game_state.pay_players(player, amount)


    def __load_cards(self) -> List[ChanceCard]:
        return [
            (
                0, 
                "Ai fost ales presedinte al consiliului de administratie. Plateste fiecarui jucatator 50$",
                self.__pay_players, 
                (50,)
            ),
            (
                1,
                "Iesi din inchisoare gratuit. Acest card poate fi pastrat pana cand este folosit sau vandut",
                self.__receive_get_out_of_jail_card,
                ()
            ),
            (
                2, 
                "Intoarce-te trei spatii",
                self.__move_player_backwards,
                (3,)
            ),
            (
                3,
                "Du-te la inchisoare. Du-te direct la inchisoare. Nu treci pe START. Nu colectezi 200$",
                self.__move_player_to_jail,
                ()
            ),
            (
                4,
                "Avanseaza la urmatoarea Gara. Daca proprietatea este nevanduta, poti sa o cumperi de la banca. Daca alt jucator o detine, platesti de doua ori chiria. Daca treci pe START, colectezi 200$",
                self.__move_player_to_nearest_railway,
                (2,)
            ),
            (
                5, 
                "Avanseaza la urmatoarea Gara. Daca proprietatea este nevanduta, poti sa o cumperi de la banca. Daca alt jucator o detine, platesti de doua ori chiria. Daca treci pe START, colectezi 200$",
                self.__move_player_to_nearest_railway,
                (2,)
            ),
            (
                6,
                "Mergi la Gara Progresul. Daca treci pe START, colectezi 200$",
                self.__move_player_to_property,
                ("Gara Progresul",)
            ),
            (
                7, 
                "Avanseaza la START. Colectezi 200$",
                self.__move_player_to_start,
                ()
            ),
            (
                8,
                "Efectueaza reparatii la toate proprietatile tale. Pentru fiecare casa platesti 25$, pentru fiecare hotel platesti 100$",
                self.__pay_tax_for_buildings,
                ()
            ),
            (
                9,
                "Avanseaza la cea mai apropiata Utilitate. Daca proprietatea este nevanduta, poti sa o cumperi de la banca. Daca alt jucator o detine, platesti de zece ori valoarea zarurilor. Daca treci pe START, colectezi 200$",
                self.__move_player_to_nearest_utility,
                ()
            ),
            (
                10,
                "Imprumutul pentru cladirile tale a ajuns la maturenitate. Colecteaza 150$",
                self.__receive_income,
                (150,)
            ),
            (
                11,
                "Deplaseaza-te la B-dul Primaverii",
                self.__move_player_to_property,
                ("B-dul Primaverii",)
            ),
            (
                12,
                "Avanseaza la Titan. Daca treci pe START, colectezi 200$",
                self.__move_player_to_property,
                ("Titan",)
            ),
            (
                13,
                "Avanseaza la B-dul Eroiloe. Daca treci pe START, colectezi 200$",
                self.__move_player_to_property,
                ("B-dul Eroilor",)
            ),
            (
                14,
                "Banca iti plateste dividendele. Colecteaza 50$",
                self.__receive_income,
                (50,)
            ),
            (
                15,
                "Amenda pentru exces de viteza. Plateste 15$",
                self.__pay_tax,
                (15,)
            )
        ]


if __name__ == "__main__":
    from game.player import Player
    from models.property_group import PropertyGroup

    players = [Player("Player 1"), Player("Player 2")]
    game_state = GameState(players)
    brown = game_state.board.get_properties_by_group(PropertyGroup.BROWN)
    game_state.buy_property(players[0], brown[0])
    game_state.buy_property(players[0], brown[1])
    game_state.houses[PropertyGroup.BROWN] = (4, players[0])
    game_state.hotels[PropertyGroup.BROWN] = (1, players[0])
    chance_manager = ChanceManager()

    for _ in range(33):
        card = chance_manager.draw_card(game_state, players[0])
        print()
        card.action(*card.args)