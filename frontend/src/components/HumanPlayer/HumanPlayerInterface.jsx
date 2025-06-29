import React, { useState, useEffect } from "react";
import Alert from "../UI/Alert";
import { AlertDescription } from "../UI/Alert";
import Button from "../UI/Button";
import useGameState from "../../hooks/useGameState";
import PlayerCard from "../Cards/PlayerCard";
import MonopolyBoard from "../Board/MonopolyBoard";
import { TradeOfferModal, CreateTradeModal } from "../Modals/TradeOfferModal";
import EventFeed from "../EventFeed/EventFeed";
import DiceIcon from "../Dice/Dice";
import DecisionUI from "../Cards/DecisionCard";
import PendingDecisionCard from "../Cards/PendingDecisionCard";
import GameErrorModal from "../Modals/GameErrorModal";
import GameVictoryModal from "../Modals/GameVictoryModal";

const HumanPlayerInterface = ({ playerPort = 6060 }) => {
  const [pendingDecision, setPendingDecision] = useState(null);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showEventFeed, setShowEventFeed] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState("All");
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [showAcceptTradeModal, setShowAcceptTradeModal] = useState(false);
  const [isNetworkLoading, setIsNetworkLoading] = useState(false);
  const [gameResult, setGameResult] = useState(null);

  const {
    gameState,
    lastRoll,
    isRolling,
    currentPlayer,
    error: gameError,
    isLoading,
    actions,
    refreshGameState,
  } = useGameState();

  // Check if the game has ended
  useEffect(() => {
    const checkGameEnd = async () => {
      try {
        const response = await fetch(
          `http://localhost:${playerPort}/api/game-result`
        );
        if (response.ok) {
          const result = await response.json();
          console.log("Game result check:", result); // Debug log

          if (result.game_ended) {
            setGameResult(result);
          }
        } else {
          console.log("Game result response not ok:", response.status);
        }
      } catch (err) {
        // Game result endpoint not available or game still ongoing
        console.log("Game result check error:", err.message);
      }
    };

    // Only check for game end if we have a valid game state
    if (gameState && !gameError && !isLoading) {
      // Check immediately
      checkGameEnd();

      // Then check every 2 seconds
      const interval = setInterval(checkGameEnd, 2000);
      return () => clearInterval(interval);
    }
  }, [playerPort, gameState, gameError, isLoading]);

  useEffect(() => {
    console.log("Component state:", {
      gameResult,
      gameError,
      isLoading,
      gameState: !!gameState,
    });
  }, [gameResult, gameError, isLoading, gameState]);

  // USE Effect to handle showing modal on accept trade
  useEffect(() => {
    if (pendingDecision && pendingDecision.type === "accept_trade") {
      setShowAcceptTradeModal(true);
    }
  }, [pendingDecision]);

  // Poll for pending decisions
  useEffect(() => {
    const savedDecision = localStorage.getItem("pendingDecision");
    if (savedDecision) {
      setPendingDecision(JSON.parse(savedDecision));
    }

    const checkDecisions = async () => {
      try {
        const response = await fetch(
          `http://localhost:${playerPort}/api/pending-decision`
        );
        if (!response.ok) throw new Error("Failed to fetch decisions");
        setIsNetworkLoading(true);
        const data = await response.json();
        if (data.type !== "none") {
          setPendingDecision(data);
          setSelectedItems(new Set()); // Reset selections
          localStorage.setItem("pendingDecision", JSON.stringify(data));
          setError(null);
        }
        setIsNetworkLoading(false);
      } catch (err) {
        setError(err.message);
        setIsNetworkLoading(false);
      }
    };

    const interval = setInterval(checkDecisions, 500);
    return () => {
      clearInterval(interval);
      localStorage.removeItem("pendingDecision");
    };
  }, [playerPort]);

  // Handle decision submission
  const handleDecision = async (choice) => {
    try {
      const response = await fetch(
        `http://localhost:${playerPort}/api/decision`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ choice }),
        }
      );
      if (!response.ok) throw new Error("Failed to send decision");
      setIsNetworkLoading(true);
      setPendingDecision(null);
      setSelectedItems(new Set());
      setError(null);
      localStorage.removeItem("pendingDecision");
    } catch (err) {
      setError(err.message);
      setIsNetworkLoading(false);
    }
  };

  const isAIThinking = () => {
    if (!gameState || isLoading) return false;

    const currentPlayerName = gameState.players[gameState.currentPlayer].name;
    return !currentPlayerName.includes("Human");
  };

  // Toggle selection in multi-select scenarios
  const toggleSelection = (item) => {
    const newSelection = new Set(selectedItems);
    if (newSelection.has(item)) {
      newSelection.delete(item);
    } else {
      newSelection.add(item);
    }
    setSelectedItems(newSelection);
  };

  // If there's a game result, show victory modal
  if (gameResult && gameResult.game_ended) {
    console.log("Showing victory modal with result:", gameResult);
    return (
      <GameVictoryModal
        gameResult={gameResult}
        gameState={gameState}
        onPlayAgain={() => {
          setGameResult(null);
          window.location.reload();
        }}
        onClose={() => {
          window.close();
        }}
      />
    );
  }

  if (gameError) {
    return (
      <GameErrorModal
        error={gameError}
        onRetry={() => {
          console.log("Retrying game state fetch...");
          if (refreshGameState) {
            refreshGameState();
          }
        }}
      />
    );
  }

  return (
    <div className="w-full h-screen max-h-screen overflow-hidden flex">
      {/* TRADING MODALS */}
      {showTradeModal && (
        // Use the enhanced CreateTradeModal component
        <CreateTradeModal
          isOpen={showTradeModal}
          onClose={() => setShowTradeModal(false)} // Just hide the modal without submitting
          tradeData={pendingDecision.data}
          onSubmit={(trades) => {
            setShowTradeModal(false);
            handleDecision(trades);
          }}
        />
      )}

      {showAcceptTradeModal && (
        <TradeOfferModal
          isOpen={showAcceptTradeModal}
          onClose={() => {
            setShowAcceptTradeModal(false);
          }}
          tradeOffer={pendingDecision.data}
          onAccept={() => {
            handleDecision(true);
            setShowAcceptTradeModal(false);
          }}
          onReject={() => {
            handleDecision(false);
            setShowAcceptTradeModal(false);
          }}
        />
      )}

      {/* Players column */}
      <div className="w-1/4 h-full overflow-auto p-3 flex flex-col space-y-4">
        {gameState?.players?.map((player, index) => (
          <PlayerCard
            key={index}
            player={player}
            isCurrentPlayer={index === gameState.currentPlayer}
          />
        ))}
      </div>

      {/* Center column with board */}
      <div className="w-1/2 h-full flex items-center justify-center relative">
        {isLoading ? (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        ) : (
          <div className="h-full w-full flex items-start p-3 justify-center">
            <div className="aspect-square max-h-full max-w-full">
              <MonopolyBoard />
            </div>
          </div>
        )}
      </div>

      {/* Right column */}
      <div className="w-1/4 h-full flex flex-col">
        {/* Decision UI */}

        <div className="p-4 flex-shrink-0">
          {pendingDecision ? (
            <DecisionUI
              pendingDecision={pendingDecision}
              handleDecision={handleDecision}
              selectedItems={selectedItems}
              toggleSelection={toggleSelection}
              setShowTradeModal={setShowTradeModal}
              setShowAcceptTradeModal={setShowAcceptTradeModal}
            />
          ) : (
            <PendingDecisionCard
              handleDecision={handleDecision}
              showEventFeed={showEventFeed}
              setShowEventFeed={setShowEventFeed}
              isAIThinking={isAIThinking}
              waitingForNetwork={isNetworkLoading}
              gameState={gameState}
            />
          )}
        </div>

        {/* Event feed */}
        {showEventFeed && (
          <div className="flex-1 flex flex-col overflow-hidden px-3 pt-2">
            <div className="flex-1 overflow-auto -mx-3 px-3">
              <EventFeed
                playerPort={playerPort}
                filter={selectedEventType.toLowerCase()}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HumanPlayerInterface;
