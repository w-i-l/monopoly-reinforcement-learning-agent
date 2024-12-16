from models.community_chest_card import CommunityChestCard
from game.game_state import GameState
from random import shuffle
from typing import List

class CommunityChestManager:
    def __init__(self):
        self.community_chest_cards = self.__load_cards()
        self.__shuffle_cards()


    def __shuffle_cards(self):
        self.__shuffled_cards = list(range(len(self.community_chest_cards)))
        shuffle(self.__shuffled_cards)


    def draw_card(self, game_state: GameState, player) -> CommunityChestCard:
        if len(self.__shuffled_cards) == 0:
            self.__shuffle_cards()

        card_id = self.__shuffled_cards.pop()
        card = self.community_chest_cards[card_id]

        return CommunityChestCard(
            id=card[0],
            description=card[1],
            action=card[2],
            args=(game_state, player, *card[3])
        )
    

    def __move_player_to_start(self, game_state: GameState, player):
        start_tile = game_state.board.get_tile_by_name("Start")
        game_state.move_player_to_property(player, start_tile)

    
    def __receive_income(self, game_state: GameState, player, amount: int):
        game_state.receive_income(player, amount)


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

        tax = houses_count * 40 + hotels_count * 115
        game_state.pay_tax(player, tax)

    
    def __move_player_to_jail(self, game_state: GameState, player):
        game_state.sent_player_to_jail(player)


    def __receive_get_out_of_jail_card(self, game_state: GameState, player):
        game_state.receive_get_out_of_jail_card(player)

    
    def __receive_from_players(self, game_state: GameState, player, amount: int):
        game_state.receive_from_players(player, amount)


    def __load_cards(self) -> List[CommunityChestCard]:
        return [
            (
                0, 
                "Pentru fiecare casa pe care o detii, platesti 40$, pentru fiecare hotel platesti 115$",
                self.__pay_tax_for_buildings,
                ()
            ),
            (
                1,
                "Du-te la inchisoare. Du-te direct la inchisoare. Nu treci pe Start. Nu colectezi 200$",
                self.__move_player_to_jail,
                ()
            ),
            (
                2,
                "Iesi din inchisoare gratuit. Aceasta carte poate fi retinuta pana cand este folosita sau vanduta",
                self.__receive_get_out_of_jail_card,
                ()
            ),
            (
                3,
                "Du-te la Start",
                self.__move_player_to_start,
                ()
            ),
            (
                4,
                "Incaseaza 10$ de la fiecare jucator",
                self.__receive_from_players,
                (10,)
            ),
            (
                5,
                "Plateste 100$",
                self.__pay_tax,
                (100,)
            ),
            (
                6,
                "Incaseaza 100$",
                self.__receive_income,
                (100,)
            ),
            (
                7,
                "Plateste 50$",
                self.__pay_tax,
                (50,)
            ),
            (
                8,
                "Incaseaza 200$",
                self.__receive_income,
                (200,)
            ),
            (
                9,
                "Incaseaza 100$",
                self.__receive_income,
                (100,)
            ),
            (
                10,
                "Plateste 50$",
                self.__pay_tax,
                (50,)
            ),
            (
                11,
                "Incaseaza 50$",
                self.__receive_income,
                (50,)
            ),
            (
                12,
                "Incaseaza 100$",
                self.__receive_income,
                (100,)
            ),
            (
                13,
                "Incaseaza 20$",
                self.__receive_income,
                (20,)
            ),
            (
                14,
                "Incaseaza 25$",
                self.__receive_income,
                (25,)
            ),
            (
                15,
                "Incaseaza 10$",
                self.__receive_income,
                (10,)
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
    chance_manager = CommunityChestManager()

    for _ in range(17):
        card = chance_manager.draw_card(game_state, players[0])
        print()
        card.action(*card.args)