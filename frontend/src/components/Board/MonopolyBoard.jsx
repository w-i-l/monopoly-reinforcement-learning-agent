import React from "react";
import BoardSquare from "./BoardSquare";
import Alert from "../UI/Alert";
import { AlertDescription } from "../UI/Alert";
import Button from "../UI/Button";
import useGameState from "../../hooks/useGameState";
import { BOARD_PROPERTIES } from "../../constants/boardProperties";

const MonopolyBoard = () => {
  const { gameState, error, isLoading, actions } = useGameState();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full w-full">
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
    gameState?.players?.forEach((player) => {
      if (player.hotels && player.hotels[propertyId]) {
        hotelCount = player.hotels[propertyId];
      }
    });
    return hotelCount;
  };

  const houses = (propertyId) => {
    let houseCount = 0;
    gameState?.players?.forEach((player) => {
      if (player.houses && player.houses[propertyId]) {
        houseCount = player.houses[propertyId];
      }
    });
    return houseCount;
  };

  return (
    <div className="w-full h-full aspect-square">
      <div className="grid grid-cols-11 grid-rows-11 h-full w-full">
        {/* Top row */}
        {BOARD_PROPERTIES.slice(0, 11).map((property, index) => (
          <BoardSquare
            key={`top-${index}`}
            property={property}
            index={index}
            players={gameState?.players || []}
            ownedProperties={gameState?.ownedProperties || []}
            mortgagedProperties={gameState?.mortgagedProperties || []}
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
              players={gameState?.players || []}
              ownedProperties={gameState?.ownedProperties || []}
              mortgagedProperties={gameState?.mortgagedProperties || []}
              houses={houses(BOARD_PROPERTIES[39 - rowIndex].id)}
              hotels={hotels(BOARD_PROPERTIES[39 - rowIndex].id)}
            />
            <div className="col-span-9 bg-green-50" /> {/* Center space */}
            <BoardSquare
              property={BOARD_PROPERTIES[11 + rowIndex]}
              index={11 + rowIndex}
              players={gameState?.players || []}
              ownedProperties={gameState?.ownedProperties || []}
              mortgagedProperties={gameState?.mortgagedProperties || []}
              houses={houses(BOARD_PROPERTIES[11 + rowIndex].id)}
              hotels={hotels(BOARD_PROPERTIES[11 + rowIndex].id)}
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
              players={gameState?.players || []}
              ownedProperties={gameState?.ownedProperties || []}
              mortgagedProperties={gameState?.mortgagedProperties || []}
              houses={houses(property.id)}
              hotels={hotels(property.id)}
            />
          ))}
      </div>
    </div>
  );
};

export default MonopolyBoard;
