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
from models.tile import Tile
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.property_group import PropertyGroup
from models.other_tiles import Taxes, Jail
from typing import Optional, Dict, Any, Tuple

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
        # TODO: Handle each player individually, rather than ending the game
        if self.game_state.player_balances[current_player] < 0:
            self.__declare_player_bankrupt(current_player)
        
        dice_roll = None

        # Handle jail logic
        if self.game_state.in_jail[current_player] == True:
            # try to roll a double
            dice_roll = self.__roll_a_dice(current_player, in_jail=True)
            if dice_roll[0] == dice_roll[1]:
                # already got out of jail from rolling doubles
                pass

            # if the player has been in jail for 3 turns, must pay fine
            elif self.game_state.turns_in_jail[current_player] == 2:
                self.__handle_paying_tax_to_get_out_of_jail(current_player)

            # try to use the escape jail card
            elif current_player.should_use_escape_jail_card(self.game_state):
                self.__handle_using_get_out_of_jail_card(current_player)

            # try to pay the fine
            elif current_player.should_pay_get_out_of_jail_fine(self.game_state):
                self.__handle_paying_tax_to_get_out_of_jail(current_player)

            # count the turn in jail
            else:
                self.__count_turn_in_jail(current_player)
                return

        # Roll the dice if the player did not roll a double in attempt to get out of jail
        if dice_roll is None:
            dice_roll = self.__roll_a_dice(current_player, in_jail=False)

        # Move the player
        self.__move_player(current_player, dice_roll)

        current_position = self.game_state.player_positions[current_player]
        current_tile = self.game_state.board.tiles[current_position]

        # check if the player went to jail
        if self.__was_player_sent_to_jail(current_player, current_tile):
            return

        # Handle landing on chance/community chest
        self.__handle_landing_on_chance(current_player, current_tile)

        # updating the player position after the card action
        current_position = self.game_state.player_positions[current_player]
        current_tile = self.game_state.board.tiles[current_position]

        # check if the player went to jail from chance card
        if self.__was_player_sent_to_jail(current_player, current_tile):
            return
        

        if isinstance(current_tile, Chance):
            self.event_manager.register_event(
                EventType.CHANCE_CARD_DRAWN,
                player=current_player,
                tile=current_tile,
                description=f"{current_player} landed on Chance"
            )
            
            dice_roll = self.dice_manager.roll()
            chance_card = self.chance_manager.draw_card(self.game_state, current_player, dice_roll)

            def action_to_perform():
                nonlocal current_position, current_tile

                # Execute the card action
                chance_card.action(*chance_card.args)

                # updating the player position after the card action
                current_position = self.game_state.player_positions[current_player]
                current_tile = self.game_state.board.tiles[current_position]

            try:
               custom_print("Performing chance card action", chance_card)

               action_to_perform()

            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="chance card action")

                # player submitted a bankruptcy request
                action_to_perform()
            
            except Exception as e:
                ErrorLogger.log_error(e)
                custom_print("Error in chance card action")
                raise e

        # `if` instead of `elif` because player can move backwards
        # and land on a community chest tile after landing on a chance tile
        if isinstance(current_tile, CommunityChest):
            self.event_manager.register_event(
                EventType.COMMUNITY_CHEST_CARD_DRAWN,
                player=current_player,
                tile=current_tile,
                description=f"{current_player} landed on Community Chest"
            )
            
            community_chest_card = self.community_chest_manager.draw_card(self.game_state, current_player)

            def action_to_perform():
                nonlocal current_position, current_tile
                
                # Execute the card action
                community_chest_card.action(*community_chest_card.args)

                # updating the player position after the card action
                current_position = self.game_state.player_positions[current_player]
                current_tile = self.game_state.board.tiles[current_position]

            try:
                custom_print("Performing community chest card action", community_chest_card)

                action_to_perform()

            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="community chest card action")

                # player submitted a bankruptcy request
                action_to_perform()

            except Exception as e:
                ErrorLogger.log_error(e)
                custom_print("Error in community chest card action")
                raise e
            
        # Check if player landed on a Tax tile
        # needs to be after community chest and chance
        # because player can land on a tax tile from those
        if isinstance(current_tile, Taxes):

            def action_to_perform():
                self.game_state.pay_tax(current_player, current_tile.tax)

            try: 
                # Register tax payment event
                self.event_manager.register_event(
                    EventType.TAX_PAID,
                    player=current_player,
                    amount=current_tile.tax,
                    description=f"{current_player} paid {current_tile.tax}₩ in taxes"
                )

                action_to_perform()

            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="paying tax")

                # player submitted a bankruptcy request
                action_to_perform()

            except Exception as e:
                ErrorLogger.log_error(e)
                raise e
        
        # Check if the player landed on an owned property
        custom_print(current_tile)
        custom_print(self.game_state.is_owned)
        if current_tile in self.game_state.is_owned and\
           current_tile not in self.game_state.properties[current_player] and\
           current_tile not in self.game_state.mortgaged_properties:
            
            def action_to_perform():
                # Process the rent payment
                self.game_state.pay_rent(current_player, current_tile, dice_roll)

            try:
                dice_roll = self.dice_manager.roll()
                
                # Find the owner of the property
                owner = None
                for player in self.players:
                    if current_tile in self.game_state.properties[player]:
                        owner = player
                        break
                
                # Calculate rent before paying it
                rent_amount = self.__calculate_rent(current_tile, owner, dice_roll)
                
                # Register rent event
                self.event_manager.register_event(
                    EventType.RENT_PAID,
                    player=current_player,
                    target_player=owner,
                    tile=current_tile,
                    amount=rent_amount,
                    description=f"{current_player} paid {rent_amount}₩ rent to {owner} for {current_tile}"
                )
                
                action_to_perform()
            
            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="paying rent")

                # player submitted a bankruptcy request
                action_to_perform()

            except Exception as e:
                ErrorLogger.log_error(e)
                custom_print("Player does not have enough balance to pay rent")
                raise e

        # Check if the player landed on an unowned property
        elif current_tile not in self.game_state.is_owned:
            if isinstance(current_tile, Property) or isinstance(current_tile, Railway) or isinstance(current_tile, Utility):
                if current_player.should_buy_property(self.game_state, current_tile):

                    def action_to_perform():
                        # Process the purchase
                        self.game_state.buy_property(current_player, current_tile) 

                    try:
                        # Register property purchase event
                        price = getattr(current_tile, 'price', 0)
                        self.event_manager.register_event(
                            EventType.PROPERTY_PURCHASED,
                            player=current_player,
                            tile=current_tile,
                            amount=price,
                            description=f"{current_player} purchased {current_tile} for {price}₩"
                        )
                        
                        action_to_perform()
                    
                    except NotEnoughBalanceException as e:
                        self.__handle_bankruptcy(current_player, e.price, reason="buying property")

                        # player submitted a bankruptcy request
                        action_to_perform()

                    except Exception as e:
                        ErrorLogger.log_error(e)
                        custom_print("Player does not have enough balance to buy the property")
                        raise e
                else:
                    # TODO: Implement auction logic when player doesn't buy
                    self.event_manager.register_event(
                        EventType.AUCTION_STARTED,
                        player=current_player,
                        tile=current_tile,
                        description=f"{current_player} chose not to purchase {current_tile}"
                    )
                    # Placeholder for auction implementation
                    pass

        # Check if the player wants to trade
        trade_offers = current_player.get_trade_offers(self.game_state)
        if trade_offers and trade_offers != []:
            for trade_offer in trade_offers:
                self.__execute_trade(trade_offer)

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


    def __execute_trade(self, trade_offer):
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
            

    def __handle_downgrading_suggestions(self, current_player):
        suggestions = current_player.get_downgrading_suggestions(self.game_state)
        
        if not suggestions:
            return

        for suggestion in suggestions:
            def report_event():
                if self.game_state.houses[suggestion][0] == 4:
                    self.event_manager.register_event(
                        EventType.HOTEL_SOLD,
                        player=current_player,
                        property_group=suggestion,
                        description=f"{current_player} sold a hotel from {suggestion}"
                    )
                else:
                    self.event_manager.register_event(
                        EventType.HOUSE_SOLD,
                        player=current_player,
                        property_group=suggestion,
                        description=f"{current_player} sold a house from {suggestion}"
                    )

            try:
                self.game_state.downgrade_property_group(current_player, suggestion)
                report_event()

            except Exception as e:
                ErrorLogger.log_error(e)
                return -1
            

    def __handle_unmortgaging_suggestions(self, current_player):
        suggestions = current_player.get_unmortgaging_suggestions(self.game_state)
        for suggestion in suggestions:
            def report_event():
                self.event_manager.register_event(
                    EventType.PROPERTY_UNMORTGAGED,
                    player=current_player,
                    tile=suggestion,
                    description=f"{current_player} unmortgaged {suggestion}"
                )

            try:
                self.game_state.unmortgage_property(current_player, suggestion)
                report_event()

            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="unmortgaging property")

                # player submitted a bankruptcy request
                self.game_state.unmortgage_property(current_player, suggestion)
                report_event()

            except Exception as e:
                # TODO: Handle error
                ErrorLogger.log_error(e)
                return -1
    
            
    def __handle_mortgaging_suggestions(self, current_player):
        suggestions = current_player.get_mortgaging_suggestions(self.game_state)
        for suggestion in suggestions:
            def report_event():
                self.event_manager.register_event(
                    EventType.PROPERTY_MORTGAGED,
                    player=current_player,
                    tile=suggestion,
                    description=f"{current_player} mortgaged {suggestion}"
                )

            try:
                self.game_state.mortgage_property(current_player, suggestion)
                report_event()
            
            except Exception as e:
                ErrorLogger.log_error(e)
                return -1
            
    def __handle_upgrading_suggestions(self, current_player):
        suggestions = current_player.get_upgrading_suggestions(self.game_state)
        for suggestion in suggestions:

            def report_event():
                if self.game_state.hotels[suggestion][0] == 1:
                    self.event_manager.register_event(
                        EventType.HOTEL_BUILT,
                        player=current_player,
                        property_group=suggestion,
                        description=f"{current_player} built a hotel on {suggestion}"
                    )
                else:
                    self.event_manager.register_event(
                        EventType.HOUSE_BUILT,
                        player=current_player,
                        property_group=suggestion,
                        description=f"{current_player} built a house on {suggestion}"
                    )

            try:
                self.game_state.update_property_group(current_player, suggestion)
                report_event()

            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="upgrading property")

                # player submitted a bankruptcy request
                self.game_state.update_property_group(current_player, suggestion)
                report_event()
                return

            except Exception as e:
                ErrorLogger.log_error(e)
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


    def __calculate_rent(self, property, owner, dice_roll: tuple[int, int] = None) -> int:
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
    

    def __handle_bankruptcy(self, current_player: Player, amount: int, reason: Optional[str] = None):
        self.event_manager.register_event(
            EventType.PLAYER_DID_NOT_HAVE_ENOUGH_MONEY,
            player=current_player,
            amount=amount,
            reason=reason,
            description=f"{current_player} did not have enough money to pay {amount}₩ for {reason}"
        )

        bankruptcy_request = current_player.handle_bankruptcy(self.game_state, amount)
        if bankruptcy_request.is_empty():
            # Player is bankrupt
            self.__declare_player_bankrupt(current_player)
        
        # execute bankruptcy request
        else:
            # erase the trade offers
            bankruptcy_request.trade_offers = []

            try:
                # complete the bankruptcy request
                self.game_state.complete_bankruptcy_request(current_player, bankruptcy_request)

                # execute trades with trade manager
                trade_offers = bankruptcy_request.trade_offers
                for trade_offer in trade_offers:
                    self.__execute_trade(trade_offer)

                # check if the player indeed fulfilled the bankruptcy request
                if self.game_state.player_balances[current_player] < amount:
                    # player is bankrupt
                    self.__declare_player_bankrupt(current_player)

            except NotEnoughBalanceException as e:
                # player is bankrupt
                self.__declare_player_bankrupt(current_player)

            except Exception as e:
                # something happened no need to continue
                ErrorLogger.log_error(e)
                raise e
                # self.__declare_player_bankrupt(current_player)


    def __declare_player_bankrupt(self, current_player: Player):
        # This will signal that a player is bankrupt
        # the proper way to handle it should be decided from outside
        # in case of a 2 players game, the game will end

        self.event_manager.register_event(
            EventType.PLAYER_BANKRUPT,
            player=current_player,
            amount=self.game_state.player_balances[current_player]
        )
        custom_print(f"{current_player} is bankrupt")
        custom_print("GAME OVER")
        # return -1
        raise BankrupcyException(current_player.name)
    

    def __handle_paying_tax_to_get_out_of_jail(self, current_player: Player):
        try:
            self.game_state.pay_get_out_of_jail_fine(current_player)
            self.event_manager.register_event(
                EventType.PLAYER_GOT_OUT_OF_JAIL,
                player=current_player,
                amount=self.game_state.board.get_jail_fine(),
                description=f"{current_player} paid {self.game_state.board.get_jail_fine()}₩ to get out of jail"
            )
            self.event_manager.register_event(
                EventType.MONEY_PAID,
                player=current_player,
                amount=self.game_state.board.get_jail_fine(),
                description=f"{current_player} paid {self.game_state.board.get_jail_fine()}₩ jail fine"
            )

        except NotEnoughBalanceException as e:
            self.__handle_bankruptcy(current_player, e.price, reason="paying jail fine")
            self.game_state.pay_get_out_of_jail_fine(current_player)

        except Exception as e:
            ErrorLogger.log_error(e)
            raise e
        
    
    def __handle_using_get_out_of_jail_card(self, current_player: Player):
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

    
    def __roll_a_dice(self, current_player: str, in_jail: bool) -> Tuple[int, int]:
        dice_roll = self.dice_manager.roll()
            
        self.event_manager.register_event(
            EventType.DICE_ROLLED,
            player=current_player,
            dice=dice_roll,
            additional_data={"in_jail": True} if in_jail else {}
        )
        
        if dice_roll[0] == dice_roll[1]:
            if in_jail:
                self.game_state.get_out_of_jail(current_player)
                self.event_manager.register_event(
                    EventType.PLAYER_GOT_OUT_OF_JAIL,
                    player=current_player,
                    description=f"{current_player} got out of jail by rolling doubles"
                )
            else:
                self.event_manager.register_event(
                    EventType.DOUBLES_ROLLED,
                    player=current_player,
                    dice=dice_roll
                )
        
        custom_print(f"{current_player} rolled {dice_roll[0]} and {dice_roll[1]}")
        return dice_roll
    

    def __count_turn_in_jail(self, current_player: Player):
        self.game_state.count_turn_in_jail(current_player)
        self.event_manager.register_event(
            EventType.TURN_ENDED,
            player=current_player,
            description=f"{current_player} remains in jail for turn {self.game_state.turns_in_jail[current_player]}"
        )
        self.__handle_in_jail_actions(current_player)


    def __move_player(self, current_player: Player, dice_roll: Tuple[int, int]):
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
                    description=f"{current_player} passed GO and collected 200₩"
                )
                self.event_manager.register_event(
                    EventType.MONEY_RECEIVED,
                    player=current_player,
                    amount=200,
                    description=f"{current_player} collected 200₩ for passing GO"
                )
            
            # Register player movement event
            current_tile = self.game_state.board.tiles[new_position]
            self.event_manager.register_event(
                EventType.PLAYER_MOVED,
                player=current_player,
                tile=current_tile,
                additional_data={"position": new_position, "dice_roll": dice_roll}
            )
            
        except NotEnoughBalanceException as e:
            self.__handle_bankruptcy(current_player, e.price, reason="moving player")

        except Exception as e:
            ErrorLogger.log_error(e)
            raise e
        

    def __was_player_sent_to_jail(self, current_player: Player, current_tile: Tile) -> bool:
        if isinstance(current_tile, Jail) and self.game_state.in_jail[current_player]:
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
            return True
        return False
    

    def __handle_landing_on_chance(self, current_player: Player, current_tile: Tile):
        # Handle landing on chance/community chest
        if isinstance(current_tile, Chance):
            self.event_manager.register_event(
                EventType.CHANCE_CARD_DRAWN,
                player=current_player,
                tile=current_tile,
                description=f"{current_player} landed on Chance"
            )
            
            dice_roll = self.dice_manager.roll()
            chance_card = self.chance_manager.draw_card(self.game_state, current_player, dice_roll)
            try:
                custom_print("Performing chance card action", chance_card)
                # Execute the card action
                chance_card.action(*chance_card.args)

            except NotEnoughBalanceException as e:
                self.__handle_bankruptcy(current_player, e.price, reason="chance card action")

                # Execute the card action
                chance_card.action(*chance_card.args)
            
            except Exception as e:
                ErrorLogger.log_error(e)
                custom_print("Error in chance card action")
                raise e