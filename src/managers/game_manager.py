from typing import List
from game.player import Player
from game.game_state import GameState
from managers.dice_manager import DiceManager
from managers.chance_manager import ChanceManager
from managers.community_chest_manager import CommunityChestManager
from exceptions.exceptions import *
from models.other_tiles import Chance, CommunityChest
from utils.logger import ErrorLogger
from managers.trade_manager import TradeManager
from managers.event_manager import EventManager, EventType, Event
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.property_group import PropertyGroup
from models.other_tiles import Taxes, Jail

CAN_PRINT = False
def custom_print(*args):
    if CAN_PRINT:
        print(*args)

class GameManager:
    def __init__(self, players: List[Player]):
        self.players = players
        self.game_state = GameState(players)
        
        # Initialize the EventManager
        self.event_manager = EventManager(self.game_state)
        
        # Initialize other managers
        self.dice_manager = DiceManager()
        self.chance_manager = ChanceManager()
        self.community_chest_manager = CommunityChestManager()
        self.trade_manager = TradeManager()

        self.chance_manager.event_manager = self.event_manager
        self.community_chest_manager.event_manager = self.event_manager
        self.trade_manager.set_event_manager(self.event_manager)
        
        # Register game started event
        self.event_manager.register_event(
            EventType.GAME_STARTED,
            player=players[0],  # Use first player as reference
            description="Monopoly game has started"
        )

    def play_turn(self):
        current_player_index = self.game_state.current_player_index
        current_player = self.players[current_player_index]
        
        # Register turn started event
        self.event_manager.register_event(
            EventType.TURN_STARTED,
            player=current_player
        )

        # Check for bankruptcy
        if self.game_state.player_balances[current_player] < 0:
            self.event_manager.register_event(
                EventType.PLAYER_BANKRUPT,
                player=current_player,
                amount=self.game_state.player_balances[current_player]
            )
            custom_print(f"{current_player} is bankrupt")
            custom_print("GAME OVER")
            return -1
        
        dice_roll = None

        # Handle jail logic
        if self.game_state.in_jail[current_player]:
            # try to roll a double
            dice_roll = self.dice_manager.roll()
            
            self.event_manager.register_event(
                EventType.DICE_ROLLED,
                player=current_player,
                dice=dice_roll,
                additional_data={"in_jail": True}
            )
            
            if dice_roll[0] == dice_roll[1]:
                self.game_state.get_out_of_jail(current_player)
                self.event_manager.register_event(
                    EventType.PLAYER_GOT_OUT_OF_JAIL,
                    player=current_player,
                    description=f"{current_player} got out of jail by rolling doubles"
                )

            # if the player has been in jail for 3 turns, must pay fine
            elif self.game_state.turns_in_jail[current_player] == 2:
                try:
                    self.game_state.pay_get_out_of_jail_fine(current_player)
                    self.event_manager.register_event(
                        EventType.PLAYER_GOT_OUT_OF_JAIL,
                        player=current_player,
                        amount=self.game_state.board.get_jail_fine(),
                        description=f"{current_player} paid ${self.game_state.board.get_jail_fine()} to get out of jail"
                    )
                    self.event_manager.register_event(
                        EventType.MONEY_PAID,
                        player=current_player,
                        amount=self.game_state.board.get_jail_fine(),
                        description=f"{current_player} paid ${self.game_state.board.get_jail_fine()} jail fine"
                    )
                except Exception as e:
                    if isinstance(e, NotEnoughBalanceException):
                        self.event_manager.register_event(
                            EventType.PLAYER_BANKRUPT,
                            player=current_player,
                            amount=self.game_state.player_balances[current_player]
                        )
                        custom_print(f"{current_player} is bankrupt")
                        custom_print("GAME OVER")
                        return -1

            # try to use the escape jail card
            elif current_player.should_use_escape_jail_card(self.game_state):
                self.game_state.use_escape_jail_card(current_player)

                # remove the escape jail card from the player
                if self.community_chest_manager.get_out_of_jail_card_owner == current_player:
                    self.community_chest_manager.use_get_out_of_jail_card(current_player)
                elif self.chance_manager.get_out_of_jail_card_owner == current_player:
                    self.chance_manager.use_get_out_of_jail_card(current_player)

                self.event_manager.register_event(
                    EventType.GET_OUT_OF_JAIL_CARD_USED,
                    player=current_player,
                    description=f"{current_player} used a Get Out of Jail Free card"
                )
                self.event_manager.register_event(
                    EventType.PLAYER_GOT_OUT_OF_JAIL,
                    player=current_player,
                    description=f"{current_player} got out of jail with a card"
                )

            # try to pay the fine
            elif current_player.should_pay_get_out_of_jail_fine(self.game_state):
                try:
                    self.game_state.pay_get_out_of_jail_fine(current_player)
                    self.event_manager.register_event(
                        EventType.PLAYER_GOT_OUT_OF_JAIL,
                        player=current_player,
                        amount=self.game_state.board.get_jail_fine(),
                        description=f"{current_player} paid ${self.game_state.board.get_jail_fine()} to get out of jail"
                    )
                    self.event_manager.register_event(
                        EventType.MONEY_PAID,
                        player=current_player,
                        amount=self.game_state.board.get_jail_fine(),
                        description=f"{current_player} paid ${self.game_state.board.get_jail_fine()} jail fine"
                    )
                except Exception as e:
                    if isinstance(e, NotEnoughBalanceException):
                        self.event_manager.register_event(
                            EventType.PLAYER_BANKRUPT,
                            player=current_player,
                            amount=self.game_state.player_balances[current_player]
                        )
                        custom_print(f"{current_player} is bankrupt")
                        custom_print("GAME OVER")
                        return -1

            # count the turn in jail
            else:
                self.game_state.count_turn_in_jail(current_player)
                self.event_manager.register_event(
                    EventType.TURN_ENDED,
                    player=current_player,
                    description=f"{current_player} remains in jail for turn {self.game_state.turns_in_jail[current_player]}"
                )
                self.__handle_in_jail_actions(current_player)
                return

        # Roll the dice if the player did not roll a double in attempt to get out of jail
        if dice_roll is None:
            dice_roll = self.dice_manager.roll()
            
            self.event_manager.register_event(
                EventType.DICE_ROLLED,
                player=current_player,
                dice=dice_roll
            )
            
            if dice_roll[0] == dice_roll[1]:
                self.event_manager.register_event(
                    EventType.DOUBLES_ROLLED,
                    player=current_player,
                    dice=dice_roll
                )
            
            custom_print(f"{current_player} rolled {dice_roll[0]} and {dice_roll[1]}")

        # Move the player
        try:
            old_position = self.game_state.player_positions[current_player]
            self.game_state.move_player(current_player, dice_roll)
            new_position = self.game_state.player_positions[current_player]
            
            # Check if player passed GO
            if new_position < old_position and not self.game_state.in_jail[current_player]:
                self.event_manager.register_event(
                    EventType.PLAYER_PASSED_GO,
                    player=current_player,
                    amount=200,
                    description=f"{current_player} passed GO and collected $200"
                )
                self.event_manager.register_event(
                    EventType.MONEY_RECEIVED,
                    player=current_player,
                    amount=200,
                    description=f"{current_player} collected $200 for passing GO"
                )
            
            # Register player movement event
            current_tile = self.game_state.board.tiles[new_position]
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=current_player,
                tile=current_tile,
                additional_data={"position": new_position, "dice_roll": dice_roll}
            )
            
        except Exception as e:
            # Landed on a tax tile
            if isinstance(e, NotEnoughBalanceException):
                self.event_manager.register_event(
                    EventType.PLAYER_BANKRUPT,
                    player=current_player,
                    amount=self.game_state.player_balances[current_player]
                )
                custom_print(f"{current_player} is bankrupt")
                custom_print("GAME OVER")
                return -1

        
        current_position = self.game_state.player_positions[current_player]
        tile = self.game_state.board.tiles[current_position]

        # check if the player went to jail
        if isinstance(tile, Jail) and self.game_state.in_jail[current_player]:
            self.event_manager.register_event(
                EventType.PLAYER_WENT_TO_JAIL,
                player=current_player,
                description=f"{current_player} was sent to jail"
            )

            self.event_manager.register_event(
                EventType.TURN_ENDED,
                player=current_player,
                description=f"{current_player}'s turn ended"
            )
            return

        # Check if player landed on a Tax tile
        if isinstance(tile, Taxes):
            try: 
                self.game_state.pay_tax(current_player, tile.tax)
                self.event_manager.register_event(
                    EventType.TAX_PAID,
                    player=current_player,
                    amount=tile.tax,
                    description=f"{current_player} paid ${tile.tax} in taxes"
                )
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    self.event_manager.register_event(
                        EventType.PLAYER_BANKRUPT,
                        player=current_player,
                        amount=self.game_state.player_balances[current_player]
                    )
                    custom_print(f"{current_player} is bankrupt")
                    custom_print("GAME OVER")
                    return -1

        
        # Handle landing on chance/community chest
        if isinstance(tile, Chance):
            self.event_manager.register_event(
                EventType.CHANCE_CARD_DRAWN,
                player=current_player,
                tile=tile,
                description=f"{current_player} landed on Chance"
            )
            
            dice_roll = self.dice_manager.roll()
            chance_card = self.chance_manager.draw_card(self.game_state, current_player, dice_roll)
            try:
                custom_print("Performing chance card action", chance_card)
                
                # Execute the card action
                chance_card.action(*chance_card.args)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    self.event_manager.register_event(
                        EventType.PLAYER_BANKRUPT,
                        player=current_player,
                        amount=self.game_state.player_balances[current_player]
                    )
                    custom_print(f"{current_player} is bankrupt")
                    custom_print("GAME OVER")
                    return -1
                
                ErrorLogger.log_error(e)
                custom_print("Error in chance card action")
                return -1

        elif isinstance(tile, CommunityChest):
            self.event_manager.register_event(
                EventType.COMMUNITY_CHEST_CARD_DRAWN,
                player=current_player,
                tile=tile,
                description=f"{current_player} landed on Community Chest"
            )
            
            community_chest_card = self.community_chest_manager.draw_card(self.game_state, current_player)
            try:
                custom_print("Performing community chest card action", community_chest_card)
                
                # Execute the card action
                community_chest_card.action(*community_chest_card.args)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    self.event_manager.register_event(
                        EventType.PLAYER_BANKRUPT,
                        player=current_player,
                        amount=self.game_state.player_balances[current_player]
                    )
                    custom_print(f"{current_player} is bankrupt")
                    custom_print("GAME OVER")
                    return -1
                
                ErrorLogger.log_error(e)
                custom_print("Error in community chest card action")
                return -1
        
        # Check if the player landed on an owned property
        custom_print(tile)
        custom_print(self.game_state.is_owned)
        if tile in self.game_state.is_owned and\
           tile not in self.game_state.properties[current_player] and\
           tile not in self.game_state.mortgaged_properties:
            try:
                dice_roll = self.dice_manager.roll()
                
                # Find the owner of the property
                owner = None
                for player in self.players:
                    if tile in self.game_state.properties[player]:
                        owner = player
                        break
                
                # Calculate rent before paying it
                rent_amount = self._calculate_rent(tile, owner, dice_roll)
                
                # Register rent event
                self.event_manager.register_event(
                    EventType.RENT_PAID,
                    player=current_player,
                    target_player=owner,
                    tile=tile,
                    amount=rent_amount,
                    description=f"{current_player} paid ${rent_amount} rent to {owner} for {tile}"
                )
                
                # Process the rent payment
                self.game_state.pay_rent(current_player, tile, dice_roll)
                
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    self.event_manager.register_event(
                        EventType.PLAYER_BANKRUPT,
                        player=current_player,
                        amount=self.game_state.player_balances[current_player]
                    )
                    custom_print(f"{current_player} is bankrupt")
                    custom_print("GAME OVER")
                    return -1
                
                # Other errors
                ErrorLogger.log_error(e)
                custom_print("Player does not have enough balance to pay rent")
                return -1

        # Check if the player landed on an unowned property
        elif tile not in self.game_state.is_owned:
            if current_player.should_buy_property(self.game_state, tile):
                try:
                    # Register property purchase event
                    price = getattr(tile, 'price', 0)
                    self.event_manager.register_event(
                        EventType.PROPERTY_PURCHASED,
                        player=current_player,
                        tile=tile,
                        amount=price,
                        description=f"{current_player} purchased {tile} for ${price}"
                    )
                    
                    # Process the purchase
                    self.game_state.buy_property(current_player, tile)
                    
                except Exception as e:
                    if isinstance(e, NotEnoughBalanceException):
                        self.event_manager.register_event(
                            EventType.MONEY_PAID,
                            player=current_player,
                            amount=price,
                            description=f"{current_player} was unable to buy {tile} due to insufficient funds"
                        )
                        custom_print(f"{current_player} was unable to buy the property")
                    
                    # Other errors
                    ErrorLogger.log_error(e)
                    custom_print("Player does not have enough balance to buy the property")
                    return -1
            else:
                # TODO: Implement auction logic when player doesn't buy
                self.event_manager.register_event(
                    EventType.AUCTION_STARTED,
                    player=current_player,
                    tile=tile,
                    description=f"{current_player} chose not to purchase {tile}, starting auction"
                )
                # Placeholder for auction implementation
                pass

        # Check if the player wants to trade
        trade_offers = current_player.get_trade_offers(self.game_state)
        if trade_offers and trade_offers != []:
            for trade_offer in trade_offers:
                # Register trade offer event
                self.event_manager.register_event(
                    EventType.TRADE_OFFERED,
                    player=trade_offer.source_player,
                    target_player=trade_offer.target_player,
                    additional_data={"trade_offer": trade_offer},
                    description=f"{trade_offer.source_player} offered a trade to {trade_offer.target_player}"
                )
                
                # Process the trade
                self.trade_manager.execute_trade(
                    trade_offer, 
                    self.game_state,
                    community_chest_manager=self.community_chest_manager,
                    chance_manager=self.chance_manager
                )

        # Check if the player wants to downgrade properties
        self.__handle_downgrading_suggestions(current_player)

        # Check if the player wants to mortgage properties
        self.__handle_mortgaging_suggestions(current_player)

        # Check if the player wants to unmortgage properties
        self.__handle_unmortgaging_suggestions(current_player)

        # Check if the player wants to upgrade properties
        self.__handle_upgrading_suggestions(current_player)
        
        # continue playing on doubles
        if dice_roll[0] == dice_roll[1]:
            self.play_turn()
        else:
            # Register turn ended event
            self.event_manager.register_event(
                EventType.TURN_ENDED,
                player=current_player,
                description=f"{current_player}'s turn ended"
            )
            

    def __handle_downgrading_suggestions(self, current_player):
        suggestions = current_player.get_downgrading_suggestions(self.game_state)
        for suggestion in suggestions:
            try:
                self.game_state.downgrade_property_group(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                return -1
            

    def __handle_unmortgaging_suggestions(self, current_player):
        suggestions = current_player.get_unmortgaging_suggestions(self.game_state)
        for suggestion in suggestions:
            try:
                self.game_state.unmortgage_property(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle error
                ErrorLogger.log_error(e)
                return -1
    
            
    def __handle_mortgaging_suggestions(self, current_player):
        suggestions = current_player.get_mortgaging_suggestions(self.game_state)
        # custom_print("Mortgaging suggestions: ", suggestions)
        for suggestion in suggestions:
            try:
                self.game_state.mortgage_property(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                custom_print("Player does not have enough balance to mortgage the property")
                return -1
            
    def __handle_upgrading_suggestions(self, current_player):
        suggestions = current_player.get_upgrading_suggestions(self.game_state)
        # custom_print("Upgrading suggestions: ", suggestions)
        for suggestion in suggestions:
            try:
                self.game_state.update_property_group(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                custom_print("Player does not have enough balance to upgrade the property")
                return -1
            
    
    def __handle_in_jail_actions(self, current_player):
        self.__handle_downgrading_suggestions(current_player)
        self.__handle_mortgaging_suggestions(current_player)
        self.__handle_unmortgaging_suggestions(current_player)
        self.__handle_upgrading_suggestions(current_player)


    def change_turn(self):
        self.game_state.change_turn()
        custom_print("\n\n")
        custom_print(f"Next player: {self.players[self.game_state.current_player_index]}")
        custom_print(self.game_state.player_balances)

    def _calculate_rent(self, property, owner, dice_roll: tuple[int, int] = None) -> int:
        """Helper method to calculate rent for a property"""
        from models.property import Property
        from models.railway import Railway
        from models.utility import Utility
        
        # Change this line from game_state to self.game_state
        game_state = self.game_state
        
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