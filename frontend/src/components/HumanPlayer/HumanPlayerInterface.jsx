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
import { EventModalManager } from "../Modals/EventModalManager";

const HumanPlayerInterface = ({ playerPort = 6060 }) => {
  const [pendingDecision, setPendingDecision] = useState(null);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showEventFeed, setShowEventFeed] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState("all");
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [showAcceptTradeModal, setShowAcceptTradeModal] = useState(false);
  const [isNetworkLoading, setIsNetworkLoading] = useState(false);
  const [gameResult, setGameResult] = useState(null);

  const [eventModalsActive, setEventModalsActive] = useState(false);
  const [modalBlocking, setModalBlocking] = useState(false);

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

  const resetModalState = () => {
    setEventModalsActive(false);
    setModalBlocking(false);
  };

  useEffect(() => {
    localStorage.clear();
    sessionStorage.clear();
  }, []);

  // Handle page visibility change to reset modal state if needed
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && modalBlocking) {
        // Reset modal state when page becomes visible again
        setTimeout(resetModalState, 1000);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [modalBlocking]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      // Press Ctrl+Shift+R to reset modal state
      if (event.ctrlKey && event.shiftKey && event.key === "R") {
        console.log("Emergency modal reset triggered");
        resetModalState();
        event.preventDefault();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Check if the game has ended
  useEffect(() => {
    const checkGameEnd = async () => {
      try {
        const response = await fetch(
          `http://localhost:${playerPort}/api/game-result`
        );
        if (response.ok) {
          const result = await response.json();
          console.log("Game result check:", result);

          if (result.game_ended) {
            setGameResult(result);
            // Reset modal state if game ended
            resetModalState();
          }
        } else {
          console.log("Game result response not ok:", response.status);
        }
      } catch (err) {
        console.log("Game result check error:", err.message);
      }
    };

    if (gameState && !gameError && !isLoading) {
      checkGameEnd();
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
      eventModalsActive,
      modalBlocking,
    });
  }, [
    gameResult,
    gameError,
    isLoading,
    gameState,
    eventModalsActive,
    modalBlocking,
  ]);

  // Handle showing modal on accept trade
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
          setSelectedItems(new Set());
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

  // Handle event modal state changes with improved logic
  const handleEventModalChange = (isActive) => {
    console.log("Modal state change:", isActive);
    setEventModalsActive(isActive);
    setModalBlocking(isActive);

    // If modals become inactive, ensure DOM cleanup
    if (!isActive) {
      setTimeout(() => {
        // Double-check that modals are really inactive
        setEventModalsActive(false);
        setModalBlocking(false);
      }, 500);
    }
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
    <div className="w-full h-screen max-h-screen overflow-hidden flex relative">
      {/* Event Modal Manager - NEW */}
      <EventModalManager
        playerPort={playerPort}
        onModalChange={handleEventModalChange}
      />

      {/* Overlay to block interface when event modals are active - NEW */}
      {modalBlocking && (
        <div
          className="absolute inset-0 z-40 bg-black/20 backdrop-blur-sm pointer-events-all flex items-center justify-center"
          onClick={resetModalState} // Emergency click to reset
        >
          <div className="text-white bg-black/50 rounded-lg text-sm"></div>
        </div>
      )}

      {/* TRADING MODALS */}
      {showTradeModal && (
        <CreateTradeModal
          isOpen={showTradeModal}
          onClose={() => setShowTradeModal(false)}
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

        {/* Event Modal Status Indicator */}
        {eventModalsActive && (
          <div className="absolute top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 z-30">
            <div className="animate-pulse w-2 h-2 bg-white rounded-full"></div>
            <span className="text-sm font-medium">Game Event</span>
          </div>
        )}
      </div>

      {/* Right column */}
      <div className="w-1/4 h-full flex flex-col">
        {/* Decision UI */}
        <div className="p-3 flex-shrink-0">
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
              eventModalsActive={eventModalsActive} // NEW: Pass modal state
            />
          )}
        </div>
        {/* Spacer */}
        <div
          className="flex-1 flex flex-col px-3 pt-2 w-1/4"
          style={{ color: "#242424", userSelect: "none" }}
        >
          11111111111111111111111111111111111111111111111111111111111111111111111111111
          111111111111111111111111111111111111111111111111
        </div>
      </div>
    </div>
  );
};

export default HumanPlayerInterface;
