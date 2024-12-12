import React from "react";
import Button from "../UI/Button";
import DiceIcon from "../Dice/Dice";

const GameControls = ({
  currentPlayer,
  lastRoll,
  isRolling,
  canRollDice,
  canBuyProperty,
  canEndTurn,
  actions,
  onOpenMortgageModal,
}) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">
        Current Turn: {currentPlayer?.name}
      </h2>

      <div className="space-y-4">
        {/* Dice display */}
        {lastRoll && (
          <div className="flex items-center gap-4 justify-center p-4 bg-gray-50 rounded">
            <DiceIcon value={lastRoll.dice[0]} />
            <DiceIcon value={lastRoll.dice[1]} />
          </div>
        )}

        {/* Action buttons */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            onClick={actions.rollDice}
            disabled={!canRollDice}
            className="w-full"
            variant="default"
          >
            {isRolling ? "Rolling..." : "Roll Dice"}
          </Button>

          <Button
            onClick={actions.buyProperty}
            disabled={false}
            className="w-full"
            variant="default"
          >
            Buy Property
          </Button>

          <Button
            onClick={actions.payRent}
            disabled={!lastRoll}
            className="w-full"
            variant="default"
          >
            Pay Rent
          </Button>

          <Button
            onClick={onOpenMortgageModal}
            disabled={!currentPlayer?.properties.length}
            className="w-full"
            variant="default"
          >
            Mortgage
          </Button>

          <Button
            onClick={actions.endTurn}
            disabled={!canEndTurn}
            className="w-full col-span-2"
            variant="default"
          >
            End Turn
          </Button>

          {/* Building controls */}
          <Button
            onClick={() =>
              actions.placeHouse(currentPlayer?.properties[0]?.name)
            }
            disabled={!currentPlayer?.properties.length}
            className="w-full"
            variant="default"
          >
            Buy House
          </Button>

          <Button
            onClick={() =>
              actions.placeHotel(currentPlayer?.properties[0]?.name)
            }
            disabled={!currentPlayer?.properties.length}
            className="w-full"
            variant="default"
          >
            Buy Hotel
          </Button>

          <Button
            onClick={() =>
              actions.sellHouse(currentPlayer?.properties[0]?.name)
            }
            disabled={!currentPlayer?.properties.length}
            className="w-full"
            variant="default"
          >
            Sell House
          </Button>

          <Button
            onClick={() =>
              actions.sellHotel(currentPlayer?.properties[0]?.name)
            }
            disabled={!currentPlayer?.properties.length}
            className="w-full"
            variant="default"
          >
            Sell Hotel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default GameControls;
