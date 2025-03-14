from game.game_state import GameState
from models.chance_card import ChanceCard
from random import shuffle
from typing import List
from exceptions.exceptions import *
from events.events import EventType
from models.railway import Railway
from models.utility import Utility
from models.property import Property
from models.tile import Tile

CAN_PRINT = False
def custom_print(*args, **kwargs):
    if CAN_PRINT:
        print(*args, **kwargs)

class ChanceManager:
    def __init__(self):
        self.chance_cards = self.__load_cards()
        self.__shuffle_cards()
        self.get_out_of_jail_card_owner = None
        self.event_manager = None


    def set_event_manager(self, event_manager):
        """Set the event manager for this chance manager."""
        self.event_manager = event_manager


    def __shuffle_cards(self):
        self.__shuffled_cards = list(range(len(self.chance_cards)))
        shuffle(self.__shuffled_cards)


    def draw_card(self, game_state: GameState, player, dice_roll: tuple[int, int]) -> ChanceCard:
        if len(self.__shuffled_cards) == 0:
            self.__shuffle_cards()

        card_id = self.__shuffled_cards.pop(0)
        card = self.chance_cards[card_id]

        args = card[3]
        if dice_roll is not None and card_id in [6, 9, 11, 12, 13]: # Events that require dice roll
            args = (*args, dice_roll)

        get_out_of_jail_card_id = 1
        if card_id == get_out_of_jail_card_id:
            if self.get_out_of_jail_card_owner == None:
                self.get_out_of_jail_card_owner = player
                # Register card receiving event
                if self.event_manager:
                    self.event_manager.register_event(
                        EventType.GET_OUT_OF_JAIL_CARD_RECEIVED,
                        player=player,
                        description=f"{player} received a Get Out of Jail Free card"
                    )
            elif self.get_out_of_jail_card_owner is not None:
                return self.draw_card(game_state, player, dice_roll)

        # Register the card drawn event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.CHANCE_CARD_DRAWN,
                player=player,
                description=f"{player} drew Chance card: {card[1]}"
            )

        return ChanceCard(
            id=card[0],
            description=card[1],
            action=card[2],
            args=(game_state, player, *args)
        )


    def use_get_out_of_jail_card(self, player):
        if self.get_out_of_jail_card_owner is not None:
            # Register card use event
            if self.event_manager:
                self.event_manager.register_event(
                    EventType.GET_OUT_OF_JAIL_CARD_USED,
                    player=player,
                    description=f"{player} used a Get Out of Jail Free card"
                )
            self.get_out_of_jail_card_owner = None
            get_out_of_jail_card_id = 1

            # Add the card back to the bottom of the deck
            self.__shuffled_cards.append(get_out_of_jail_card_id)
            return
        
        raise NotEnoughJailCardsException(player_name=player.name)


    def update_get_out_of_jail_card_owner(self, player):
        self.get_out_of_jail_card_owner = player


    def __move_player_to_nearest_utility(self, game_state: GameState, player, dice_roll: tuple[int, int]):
        utilities = game_state.board.get_utilities()
        player_position = game_state.player_positions[player]

        # Find the nearest utility
        nearest_utility = None
        min_distance = 100
        for utility in utilities:
            distance = (utility.id - player_position) + (40 if utility.id < player_position else 0)
            if distance < min_distance:
                min_distance = distance
                nearest_utility = utility

        # Register movement event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=player,
                tile=nearest_utility,
                description=f"{player} moved to nearest utility: {nearest_utility}"
            )

        game_state.move_player_to_property(player, nearest_utility)

        # Pay rent or buy the utility
        if nearest_utility in game_state.is_owned and \
            not nearest_utility in game_state.properties[player] and\
            not nearest_utility in game_state.mortgaged_properties:
            
            # Find the owner
            owner = None
            for p in game_state.players:
                if nearest_utility in game_state.properties[p]:
                    owner = p
                    break
            
            # Calculate rent
            utility_rent = 10 * sum(dice_roll)
            
            # Register rent payment event
            if self.event_manager and owner:
                self.event_manager.register_event(
                    EventType.RENT_PAID,
                    player=player,
                    target_player=owner,
                    tile=nearest_utility,
                    amount=utility_rent,
                    dice=dice_roll,
                    description=f"{player} paid ${utility_rent} rent to {owner} for {nearest_utility}"
                )
                
            game_state.pay_rent(
                player,
                nearest_utility,
                dice_roll=dice_roll,
                utility_factor_multiplier=10
                )
        else:
            if player.should_buy_property(game_state, nearest_utility):
                # Register purchase event
                if self.event_manager:
                    self.event_manager.register_event(
                        EventType.PROPERTY_PURCHASED,
                        player=player,
                        tile=nearest_utility,
                        amount=nearest_utility.price,
                        description=f"{player} purchased {nearest_utility} for ${nearest_utility.price}"
                    )
                game_state.buy_property(player, nearest_utility)


    def __pay_tax(self, game_state: GameState, player, tax: int):
        # Register tax payment event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.TAX_PAID,
                player=player,
                amount=tax,
                description=f"{player} paid ${tax} in taxes"
            )
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
        
        # Register building tax event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.TAX_PAID,
                player=player,
                amount=tax,
                description=f"{player} paid ${tax} for building repairs (houses: {houses_count}, hotels: {hotels_count})"
            )
            
        game_state.pay_tax(player, tax)


    def __move_player_to_start(self, game_state: GameState, player):
        start_tile = game_state.board.get_tile_by_name("Start")
        
        # Register move to start event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=player,
                tile=start_tile,
                description=f"{player} moved to Start"
            )
            
            # Register collection of $200 event
            self.event_manager.register_event(
                EventType.MONEY_RECEIVED,
                player=player,
                amount=200,
                description=f"{player} collected $200 for reaching Start"
            )
            
        game_state.move_player_to_start(player)


    def __receive_income(self, game_state: GameState, player, amount: int):
        # Register income event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.MONEY_RECEIVED,
                player=player,
                amount=amount,
                description=f"{player} received ${amount} from chance card"
            )
        game_state.receive_income(player, amount)


    def __move_player_to_nearest_railway(self, game_state: GameState, player, railway_factor_multiplier: int = None):
        railways = game_state.board.get_railways()
        player_position = game_state.player_positions[player]

        # Find the nearest railway
        nearest_railway = None
        min_distance = 100
        for railway in railways:
            distance = (railway.id - player_position) + (40 if railway.id < player_position else 0)
            if distance < min_distance:
                min_distance = distance
                nearest_railway = railway

        # Register movement event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=player,
                tile=nearest_railway,
                description=f"{player} moved to nearest railway: {nearest_railway}"
            )
            
        game_state.move_player_to_property(player, nearest_railway)

        # Pay rent or buy the railway
        if nearest_railway in game_state.is_owned and \
            not nearest_railway in game_state.properties[player] and\
            not nearest_railway in game_state.mortgaged_properties:
            
            # Find the owner
            owner = None
            for p in game_state.players:
                if nearest_railway in game_state.properties[p]:
                    owner = p
                    break
                    
            # Get rent amount
            rent_index = -1
            for prop in game_state.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = nearest_railway.rent[rent_index]
            if railway_factor_multiplier:
                rent *= railway_factor_multiplier
                
            # Register rent payment event
            if self.event_manager and owner:
                self.event_manager.register_event(
                    EventType.RENT_PAID,
                    player=player,
                    target_player=owner,
                    tile=nearest_railway,
                    amount=rent,
                    description=f"{player} paid ${rent} rent to {owner} for {nearest_railway}"
                )
                
            game_state.pay_rent(player, nearest_railway, railway_factor_multiplier)

        else:
            if player.should_buy_property(game_state, nearest_railway):
                # Register purchase event
                if self.event_manager:
                    self.event_manager.register_event(
                        EventType.PROPERTY_PURCHASED,
                        player=player,
                        tile=nearest_railway,
                        amount=nearest_railway.price,
                        description=f"{player} purchased {nearest_railway} for ${nearest_railway.price}"
                    )
                game_state.buy_property(player, nearest_railway)


    def __move_player_to_jail(self, game_state: GameState, player):
        # Register jail event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.PLAYER_WENT_TO_JAIL,
                player=player,
                description=f"{player} was sent to jail"
            )
        game_state.send_player_to_jail(player)


    def __move_player_backwards(self, game_state: GameState, player, steps: int):
        old_position = game_state.player_positions[player]
        game_state.move_player_backwards(player, steps)
        new_position = game_state.player_positions[player]
        
        # Register movement event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=player,
                tile=game_state.board.tiles[new_position],
                description=f"{player} moved backwards {steps} steps to {game_state.board.tiles[new_position]}"
            )

        current_player_position = game_state.player_positions[player]
        current_tile = game_state.board.tiles[current_player_position]

        # see details about community chest/taxes implementation
        # in game_state.py
        if not isinstance(current_tile, Property):
            return

        # Handling landing on a property

        # Pay rent if the property is owned by another player
        if current_tile in game_state.is_owned and \
            not current_tile in game_state.properties[player] and\
            not current_tile in game_state.mortgaged_properties:
            
            # Find the owner
            owner = None
            for p in game_state.players:
                if current_tile in game_state.properties[p]:
                    owner = p
                    break
            
            # Get the rent amount
            rent = self.__calculate_rent(game_state, current_tile, owner)
            
            # Register rent payment event
            if self.event_manager and owner:
                self.event_manager.register_event(
                    EventType.RENT_PAID,
                    player=player,
                    target_player=owner,
                    tile=current_tile,
                    amount=rent,
                    description=f"{player} paid ${rent} rent to {owner} for {current_tile}"
                )
                
            game_state.pay_rent(player, current_tile)

        # try to buy the property if the player has enough money
        elif player.should_buy_property(game_state, current_tile):
                # Register purchase event
                if self.event_manager:
                    self.event_manager.register_event(
                        EventType.PROPERTY_PURCHASED,
                        player=player,
                        tile=current_tile,
                        amount=current_tile.price,
                        description=f"{player} purchased {current_tile} for ${current_tile.price}"
                    )
                game_state.buy_property(player, current_tile)


    def __move_player_to_property(self, game_state: GameState, player, property_name: str, dice_roll: tuple[int, int]):
        property_tile = game_state.board.get_tile_by_name(property_name)
        if property_tile is None:
            raise NoPropertyNamedException(property_name)
            
        # Register movement event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=player,
                tile=property_tile,
                description=f"{player} moved to {property_tile}"
            )
            
        game_state.move_player_to_property(player, property_tile)

        if property_tile in game_state.is_owned and \
            not property_tile in game_state.properties[player] and\
            not property_tile in game_state.mortgaged_properties:
            
            # Find the owner
            owner = None
            for p in game_state.players:
                if property_tile in game_state.properties[p]:
                    owner = p
                    break
            
            # Get the rent amount
            rent = self.__calculate_rent(game_state, property_tile, owner, dice_roll)
            
            # Register rent payment event
            if self.event_manager and owner:
                self.event_manager.register_event(
                    EventType.RENT_PAID,
                    player=player,
                    target_player=owner,
                    tile=property_tile,
                    amount=rent,
                    description=f"{player} paid ${rent} rent to {owner} for {property_tile}"
                )
            
            game_state.pay_rent(player, property_tile)

        else:
            if player.should_buy_property(game_state, property_tile):
                # Register purchase event
                if self.event_manager:
                    self.event_manager.register_event(
                        EventType.PROPERTY_PURCHASED,
                        player=player,
                        tile=property_tile,
                        amount=property_tile.price,
                        description=f"{player} purchased {property_tile} for ${property_tile.price}"
                    )
                game_state.buy_property(player, property_tile)


    def __receive_get_out_of_jail_card(self, game_state: GameState, player):
        # Register jail card event
        if self.event_manager:
            self.event_manager.register_event(
                EventType.GET_OUT_OF_JAIL_CARD_RECEIVED,
                player=player,
                description=f"{player} received a Get Out of Jail Free card"
            )
        game_state.receive_get_out_of_jail_card(player)
        

    def __pay_players(self, game_state: GameState, player, amount: int):
        # Register payment events
        if self.event_manager:
            for other_player in game_state.players:
                if other_player != player:
                    self.event_manager.register_event(
                        EventType.MONEY_PAID,
                        player=player,
                        target_player=other_player,
                        amount=amount,
                        description=f"{player} paid ${amount} to {other_player}"
                    )
                    
                    self.event_manager.register_event(
                        EventType.MONEY_RECEIVED,
                        player=other_player,
                        target_player=player,
                        amount=amount,
                        description=f"{other_player} received ${amount} from {player}"
                    )
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
                "Avanseaza la B-dul Eroilor. Daca treci pe START, colectezi 200$",
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
    

    def __calculate_rent(self, game_state, property, owner, dice_roll: tuple[int, int] = None) -> int:
        """Helper method to calculate rent for a property"""
        
        if isinstance(property, Property):
            rent = property.base_rent
            if game_state.houses[property.group][0] > 0:
                rent = property.house_rent[game_state.houses[property.group][0] - 1]
            elif game_state.hotels[property.group][0] > 0:
                rent = property.hotel_rent
            elif all(prop in game_state.properties[owner] for prop in game_state.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
                
        elif isinstance(property, Railway):
            rent_index = -1
            for prop in game_state.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = property.rent[rent_index]

        elif isinstance(property, Utility):
            dice = sum(dice_roll)
            rent = 4 * dice
            for prop in game_state.properties[owner]:
                if isinstance(prop, Utility) and prop != property:
                    rent = 10 * dice
                    
        else:
            rent = 0
            
        return rent


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
        custom_print()
        card.action(*card.args)