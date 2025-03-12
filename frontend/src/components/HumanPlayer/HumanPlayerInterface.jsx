// This would be an update to components/HumanPlayer/HumanPlayerInterface.jsx

import React, { useState, useEffect } from "react";
import Alert from "../UI/Alert";
import { AlertDescription } from "../UI/Alert";
import Button from "../UI/Button";
import useGameState from "../../hooks/useGameState";
import PlayerCard from "../Cards/PlayerCard";
import MonopolyBoard from "../Board/MonopolyBoard";
import { TradeOfferModal, CreateTradeModal } from "../Modals/TradeOfferModal";
import EventFeed from "../EventFeed/EventFeed";

const HumanPlayerInterface = ({ playerPort = 6060 }) => {
  const [pendingDecision, setPendingDecision] = useState(null);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showEventFeed, setShowEventFeed] = useState(true);
  const {
    gameState,
    lastRoll,
    isRolling,
    currentPlayer,
    error: gameError,
    isLoading,
  } = useGameState();

  // Clear pending decisions when component unmounts
  useEffect(() => {
    return () => {
      localStorage.removeItem("pendingDecision");
    };
  }, []);

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
        const data = await response.json();
        if (data.type !== "none") {
          setPendingDecision(data);
          setSelectedItems(new Set()); // Reset selections
          localStorage.setItem("pendingDecision", JSON.stringify(data));
        }
      } catch (err) {
        setError(err.message);
      }
    };

    const interval = setInterval(checkDecisions, 500);
    return () => clearInterval(interval);
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
      setPendingDecision(null);
      setSelectedItems(new Set());
      localStorage.removeItem("pendingDecision");
    } catch (err) {
      setError(err.message);
    }
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

  // UI Components
  const SelectableButton = ({
    item,
    children,
    onClick,
    selected,
    className = "",
  }) => (
    <Button
      onClick={onClick}
      className={`${className} ${selected ? "bg-blue-700" : ""}`}
    >
      {children}
      {selected && " ✓"}
    </Button>
  );

  const renderMoneyInfo = ({ balance, cost }) => (
    <div className="flex flex-col gap-1 text-sm">
      {cost && <div>Cost: ${cost}</div>}
      <div>Your Balance: ${balance}</div>
    </div>
  );

  const DecisionCard = ({ title, children, actions }) => (
    <div className="bg-white p-4 rounded-lg shadow-md mb-4">
      <h3 className="text-lg font-bold mb-3">{title}</h3>
      {(
        <Button onClick={() => handleDecision([])} className="w-full mb-2">
          Skip
        </Button>
      )}
      {children}
      {actions && <div className="mt-4 space-y-2">{actions}</div>}
    </div>
  );

  const renderMultipleActionButtons = (type) => (
    <Button
      onClick={() => handleDecision(Array.from(selectedItems))}
      disabled={selectedItems.size === 0}
      className="w-full"
    >
      {`Confirm Selected ${type} (${selectedItems.size})`}
    </Button>
  );

  // Decision UI renderer
  const renderDecisionUI = () => {
    if (!pendingDecision) return null;

    const decisions = {
      upgrade_properties: () => (
        <DecisionCard
          title="Upgrade Properties"
          actions={renderMultipleActionButtons("Upgrades")}
        >
          {renderMoneyInfo({ balance: pendingDecision.data.balance })}
          <div className="mt-4 space-y-4">
            {Object.entries(pendingDecision.data.grouped_properties).map(
              ([group, props]) => {
                const isSelected = selectedItems.has(group);
                return (
                  <div key={group} className="p-3 border rounded-md">
                    <h4 className="font-medium mb-2">{group}</h4>
                    <div className="text-sm mb-3">
                      {props.map((prop, idx) => (
                        <div key={idx}>{prop}</div>
                      ))}
                    </div>
                    <SelectableButton
                      item={group}
                      onClick={() => toggleSelection(group)}
                      selected={isSelected}
                      className="w-full"
                    >
                      Upgrade {group}
                    </SelectableButton>
                  </div>
                );
              }
            )}
          </div>
        </DecisionCard>
      ),

      mortgage_properties: () => (
        <DecisionCard
          title="Mortgage Properties"
          actions={renderMultipleActionButtons("Mortgages")}
        >
          {renderMoneyInfo({ balance: pendingDecision.data.balance })}
          <div className="space-y-2">
            {pendingDecision.data.properties.map((prop) => {
              const isSelected = selectedItems.has(prop);
              return (
                <SelectableButton
                  key={prop}
                  item={prop}
                  onClick={() => toggleSelection(prop)}
                  selected={isSelected}
                  className="w-full"
                >
                  Mortgage {prop}
                </SelectableButton>
              );
            })}
          </div>
        </DecisionCard>
      ),

      buy_property: () => (
        <DecisionCard title="Buy Property?">
          <div className="text-lg mb-2">{pendingDecision.data.property}</div>
          {renderMoneyInfo({
            balance: pendingDecision.data.balance,
            cost: pendingDecision.data.price,
          })}
          <div className="flex gap-3 mt-4">
            <Button onClick={() => handleDecision(true)} className="flex-1">
              Buy Property
            </Button>
            <Button onClick={() => handleDecision(false)} className="flex-1">
              Pass
            </Button>
          </div>
        </DecisionCard>
      ),

      accept_trade: () => (
        <TradeOfferModal
          isOpen={true}
          onClose={() => handleDecision(false)}
          tradeOffer={pendingDecision.data}
          onAccept={() => handleDecision(true)}
          onReject={() => handleDecision(false)}
        />
      ),

      create_trade: () => (
        <CreateTradeModal
          isOpen={true}
          onClose={() => handleDecision(null)}
          tradeData={pendingDecision.data}
          onSubmit={handleDecision}
        />
      ),

      pay_jail_fine: () => (
        <DecisionCard title="Pay Jail Fine?">
          {renderMoneyInfo({
            balance: pendingDecision.data.balance,
            cost: pendingDecision.data.jail_fine,
          })}
          <div className="flex gap-3 mt-4">
            <Button onClick={() => handleDecision(true)} className="flex-1">
              Pay Fine
            </Button>
            <Button onClick={() => handleDecision(false)} className="flex-1">
              Stay in Jail
            </Button>
          </div>
        </DecisionCard>
      ),

      use_jail_card: () => (
        <DecisionCard title="Use Get Out of Jail Free Card?">
          <div className="flex gap-3 mt-4">
            <Button
              onClick={() => handleDecision(true)}
              disabled={!pendingDecision.data.has_card}
              className="flex-1"
            >
              Use Card
            </Button>
            <Button onClick={() => handleDecision(false)} className="flex-1">
              Stay in Jail
            </Button>
          </div>
        </DecisionCard>
      ),
    };

    return decisions[pendingDecision.type]?.() || null;
  };

  // Player cards renderer
  const renderPlayerCards = () => (
    <div className="space-y-4">
      {gameState?.players.map((player, index) => (
        <PlayerCard
          key={index}
          player={player}
          isCurrentPlayer={index === gameState.currentPlayer}
        />
      ))}
    </div>
  );

  // Main render
  return (
    <div className="container mx-auto p-4">
      {(error || gameError) && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error || gameError}</AlertDescription>
        </Alert>
      )}

      <div className="flex gap-6">
        <div className="flex-1">
          {isLoading ? (
            <div className="flex justify-center items-center h-96">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
            </div>
          ) : (
            <MonopolyBoard />
          )}
        </div>

        <div className="w-1/3 space-y-4">
          {renderDecisionUI()}
          
          <div className="mb-4 flex justify-between">
            <Button
              onClick={() => handleDecision({ type: "create_trade" })}
              className="flex-1 mr-2"
              disabled={!currentPlayer || pendingDecision}
            >
              Propose Trade
            </Button>
            
            <Button
              onClick={() => setShowEventFeed(!showEventFeed)}
              className="px-3"
            >
              {showEventFeed ? "Hide Events" : "Show Events"}
            </Button>
          </div>
          
          {/* Event Feed toggle */}
          {showEventFeed && (
            <div className="mb-4">
              <EventFeed playerPort={playerPort} />
            </div>
          )}
          
          {renderPlayerCards()}
        </div>
      </div>
    </div>
  );
};

export default HumanPlayerInterface;