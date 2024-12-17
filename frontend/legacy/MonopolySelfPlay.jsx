import React from "react";
import BoardSquare from "../src/components/Board/BoardSquare";
import PlayerCard from "../src/components/Cards/PlayerCard";
import DiceIcon from "../src/components/Dice/Dice";
import SelectPropertyModal from "../src/components/Modals/SelectPropertyModal";
import Alert from "../src/components/UI/Alert";
import { AlertDescription } from "../src/components/UI/Alert";
import Button from "../src/components/UI/Button";
import useGameState from "../src/hooks/useGameState";
import { BOARD_PROPERTIES } from "../src/constants/boardProperties";
import GameControls from "../src/components/Board/GameControls";

const MonopolyBoard = () => {
  const {
    gameState,
    lastRoll,
    isRolling,
    error,
    isLoading,
    currentPlayer,
    canRollDice,
    canBuyProperty,
    canEndTurn,
    actions,
    isModalOpen,
    setIsModalOpen,
  } = useGameState();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Alert variant="destructive" className="m-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={actions.clearError} variant="default">
          Dismiss
        </Button>
      </div>
    );
  }

  const hotels = (propertyId) => {
    let hotelCount = 0;
    gameState.players.forEach((player) => {
      if (player.hotels && player.hotels[propertyId]) {
        hotelCount = player.hotels[propertyId];
      }
    });
    return hotelCount;
  };

  const houses = (propertyId) => {
    let houseCount = 0;
    gameState.players.forEach((player) => {
      if (player.houses && player.houses[propertyId]) {
        houseCount = player.houses[propertyId];
      }
    });
    return houseCount;
  };

  const renderBoard = () => (
    <div className="grid grid-cols-11 gap-0 border border-gray-300">
      {/* Top row */}
      {BOARD_PROPERTIES.slice(0, 11).map((property, index) => (
        <BoardSquare
          key={`top-${index}`}
          property={property}
          index={index}
          players={gameState.players}
          ownedProperties={gameState.ownedProperties}
          mortgagedProperties={gameState.mortgagedProperties}
          houses={houses(property.id)}
          hotels={hotels(property.id)}
        />
      ))}

      {/* Middle rows */}
      {[...Array(9)].map((_, rowIndex) => (
        <React.Fragment key={`row-${rowIndex}`}>
          <BoardSquare
            property={BOARD_PROPERTIES[39 - rowIndex]}
            index={39 - rowIndex}
            players={gameState.players}
            ownedProperties={gameState.ownedProperties}
            mortgagedProperties={gameState.mortgagedProperties}
            houses={houses(39 - rowIndex)}
            hotels={hotels(39 - rowIndex)}
          />
          <div className="col-span-9 bg-green-50" /> {/* Center space */}
          <BoardSquare
            property={BOARD_PROPERTIES[11 + rowIndex]}
            index={11 + rowIndex}
            players={gameState.players}
            ownedProperties={gameState.ownedProperties}
            mortgagedProperties={gameState.mortgagedProperties}
            houses={houses(11 + rowIndex)}
            hotels={hotels(11 + rowIndex)}
          />
        </React.Fragment>
      ))}

      {/* Bottom row */}
      {BOARD_PROPERTIES.slice(20, 31)
        .reverse()
        .map((property, index) => (
          <BoardSquare
            key={`bottom-${index}`}
            property={property}
            index={30 - index}
            players={gameState.players}
            ownedProperties={gameState.ownedProperties}
            mortgagedProperties={gameState.mortgagedProperties}
            houses={houses(property.id)}
            hotels={hotels(property.id)}
          />
        ))}
    </div>
  );

  const renderPlayerCards = () => (
    <div className="space-y-4">
      {gameState.players.map((player, index) => (
        <PlayerCard
          key={index}
          player={player}
          isCurrentPlayer={index === gameState.currentPlayer}
        />
      ))}
    </div>
  );

  return (
    <div className="container mx-auto p-1">
      <div className="flex gap-8">
        {/* Left side - Game board */}
        <div className="flex-1">{renderBoard()}</div>

        {/* Right side - Controls and player info */}
        <div className="w-80 space-y-6">
          <GameControls
            currentPlayer={currentPlayer}
            lastRoll={lastRoll}
            isRolling={isRolling}
            canRollDice={canRollDice}
            canBuyProperty={canBuyProperty}
            canEndTurn={canEndTurn}
            actions={actions}
            onOpenMortgageModal={() => setIsModalOpen(true)}
          />
          {renderPlayerCards()}
        </div>

        {/* Modals */}
        <SelectPropertyModal
          isOpen={isModalOpen}
          onRequestClose={() => setIsModalOpen(false)}
          properties={currentPlayer?.properties || []}
          onSelectProperty={(property) => {
            actions.mortgageProperty(property);
            setIsModalOpen(false);
          }}
        />
      </div>
    </div>
  );
};

export default MonopolyBoard;
