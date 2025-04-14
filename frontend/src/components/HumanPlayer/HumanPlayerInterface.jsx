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

const HumanPlayerInterface = ({ playerPort = 6060 }) => {
  const [pendingDecision, setPendingDecision] = useState(null);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showEventFeed, setShowEventFeed] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState("All");
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [showAcceptTradeModal, setShowAcceptTradeModal] = useState(false);
  const [isNetworkLoading, setIsNetworkLoading] = useState(false);


  const {
    gameState,
    lastRoll,
    isRolling,
    currentPlayer,
    error: gameError,
    isLoading,
    actions,
  } = useGameState();

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


  return (
    <div className="w-full h-screen max-h-screen overflow-hidden flex">
      {gameError && (
        <Alert
          variant="destructive"
          className="absolute top-0 left-0 right-0 z-50"
        >
          <AlertDescription>{error || gameError}</AlertDescription>
        </Alert>
      )}

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
