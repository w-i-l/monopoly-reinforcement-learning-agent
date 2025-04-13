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

const HumanPlayerInterface = ({ playerPort = 6060 }) => {
  const [pendingDecision, setPendingDecision] = useState(null);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [showEventFeed, setShowEventFeed] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState("All");
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [showAcceptTradeModal, setShowAcceptTradeModal] = useState(false);
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
      <Button onClick={() => handleDecision([])} className="w-full mb-2">
        Skip
      </Button>
      {children && <div className=" max-h-[30vh] overflow-auto">{children}</div>}
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

  const colorMap = {
    brown: "#845031",
    light_blue: "#c0e0f9",
    pink: "#b63785",
    orange: "#d39423",
    red: "#c3141b",
    yellow: "#fdee01",
    green: "#5aa757",
    blue: "#1166b0",
    railway: "#000000",
    utility: "#000000",
    unknown: "#cccccc",
  };

  function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
  }

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
              ([group, groupInfo]) => {
                const [props, cost] = groupInfo;
                const isSelected = selectedItems.has(group);
                return (
                  <div key={group} className="p-3 border rounded-md">
                    <div className="flex items-center justify-center mb-2">
                      <div
                        style={{
                          background: `${colorMap[group]}`,
                          paddingLeft: "4px",
                          width: "20px",
                          height: "20px",
                        }}
                      ></div>
                      <h4 className="font-medium">
                        {capitalizeFirstLetter(group)}
                      </h4>
                    </div>
                    <div className="text-sm mb-3">
                      {props.map((prop, idx) => (
                        <div key={idx}>{prop}</div>
                      ))}
                    </div>
                    <div className="text-sm mb-3">Upgrade cost: ${cost}</div>
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
        <DecisionCard title="Accept Trade?">
          <div className="text-lg mb-2">
            {pendingDecision.data.source_player} has offered you a trade:
          </div>
          <div className="flex gap-3 mt-4">
            <Button
              onClick={() => setShowAcceptTradeModal(true)}
              className="flex-1"
            >
              View Trade
            </Button>
            <Button onClick={() => handleDecision(false)} className="flex-1">
              Reject trade
            </Button>
          </div>
        </DecisionCard>
      ),

      create_trade: () => (
        <DecisionCard title="Create Trade?">
          <div className="text-lg mb-2">
            Would you like to create a trade offer?
          </div>
          <div className="flex gap-3 mt-4">
            <Button onClick={() => setShowTradeModal(true)} className="flex-1">
              Create Trade
            </Button>
            <Button onClick={() => handleDecision([])} className="flex-1">
              Skip
            </Button>
          </div>
        </DecisionCard>
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

  return (
    <div className="w-full h-screen max-h-screen overflow-hidden flex">
      {(error || gameError) && (
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
        <div className="p-3 overflow-auto">{renderDecisionUI()}</div>

        {/* Action buttons */}
        <div className="p-3 flex gap-3 border-b border-slate-200">
          <Button
            onClick={() => handleDecision([])}
            disabled={pendingDecision}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2"
          >
            Next decision
          </Button>
          
          <Button
            onClick={() => setShowEventFeed(!showEventFeed)}
            className="flex-1 bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium py-2"
          >
            {showEventFeed ? "Hide Events" : "Show Events"}
          </Button>
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
