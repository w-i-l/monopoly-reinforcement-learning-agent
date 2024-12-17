import { useState, useEffect, useCallback, useRef } from "react";
import * as gameAPI from "../services/GameAPI";
import areGameStateEqual from "../utils/compare_game_states";

const useGameState = () => {
  const [gameState, setGameState] = useState(null);
  const [lastRoll, setLastRoll] = useState(null);
  const [isRolling, setIsRolling] = useState(false);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

   const gameStateRef = useRef(null);

   const fetchGameState = useCallback(async () => {
     try {
       const data = await gameAPI.fetchGameState();
       if (!areGameStateEqual(data, gameStateRef.current)) {
         setGameState(data);
         gameStateRef.current = data;
         console.log("Game state updated");
       } else {
          console.log("Game state unchanged");
       }
     } catch (error) {
       setError(error.message);
     } finally {
       setIsLoading(false);
     }
   }, []);

   useEffect(() => {
     fetchGameState();

     const intervalId = setInterval(() => {
       fetchGameState();
     }, 500);

     return () => {
       clearInterval(intervalId);
     };
   }, [fetchGameState]);  

  // Game actions
  const actions = {
    rollDice: async () => {
      setIsRolling(true);
      try {
        const data = await gameAPI.rollDice();
        setLastRoll(data);
        await fetchGameState();
        return data;
      } catch (error) {
        setError(error.message);
        throw error;
      } finally {
        setIsRolling(false);
      }
    },

    buyProperty: async () => {
      try {
        await gameAPI.buyProperty();
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    endTurn: async () => {
      try {
        await gameAPI.endTurn();
        setLastRoll(null);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    payRent: async () => {
      try {
        await gameAPI.payRent();
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    mortgageProperty: async (propertyName) => {
      try {
        await gameAPI.mortgageProperty(propertyName);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    unmortgageProperty: async (propertyName) => {
      try {
        await gameAPI.unmortgageProperty(propertyName);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    placeHouse: async (propertyName) => {
      try {
        await gameAPI.placeHouse(propertyName);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    placeHotel: async (propertyName) => {
      try {
        await gameAPI.placeHotel(propertyName);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    sellHouse: async (propertyName) => {
      try {
        await gameAPI.sellHouse(propertyName);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    sellHotel: async (propertyName) => {
      try {
        await gameAPI.sellHotel(propertyName);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    drawCard: async (cardType) => {
      try {
        const cardData = await gameAPI.drawCard(cardType);
        await fetchGameState();
        return cardData;
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    proposeTrade: async (tradeDetails) => {
      try {
        await gameAPI.proposeTrade(tradeDetails);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    respondToTrade: async (tradeId, accept) => {
      try {
        await gameAPI.respondToTrade(tradeId, accept);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
        throw error;
      }
    },

    // Helper methods
    clearError: () => setError(null),
    resetLastRoll: () => setLastRoll(null),
  };

  // Computed properties
  const currentPlayer = gameState?.players[gameState.currentPlayer] || null;
  const isCurrentPlayersTurn = gameState?.currentPlayer !== undefined;
  const canRollDice = isCurrentPlayersTurn && !lastRoll && !isRolling;
  const canBuyProperty = lastRoll && gameState?.canBuyProperty;
  const canEndTurn = lastRoll && !isRolling;

  return {
    // State
    gameState,
    lastRoll,
    isRolling,
    error,
    isLoading,
    isModalOpen,
    setIsModalOpen,

    // Actions
    actions,

    // Computed properties
    currentPlayer,
    isCurrentPlayersTurn,
    canRollDice,
    canBuyProperty,
    canEndTurn,

    // Utilities
    refreshGameState: fetchGameState,
  };
};

export default useGameState;
