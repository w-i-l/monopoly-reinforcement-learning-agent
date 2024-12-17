import React, { useState, useEffect } from "react";
import MonopolyBoard from "../Board/MonopolyBoard";
import Alert from "../UI/Alert";
import { AlertDescription } from "../UI/Alert";
import Button from "../UI/Button";
import useGameState from "../../hooks/useGameState";
import PlayerCard from "../Cards/PlayerCard";

const HumanPlayerInterface = ({ playerPort = 6060 }) => {
  const [pendingDecision, setPendingDecision] = useState(null);
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
          localStorage.setItem("pendingDecision", JSON.stringify(data));
        }
      } catch (err) {
        setError(err.message);
      }
    };

    const interval = setInterval(checkDecisions, 500);
    return () => clearInterval(interval);
  }, [playerPort]);

  const handleDecision = async (choice) => {
    try {
      const response = await fetch(
        `http://localhost:${playerPort}/api/decision`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({ choice }),
        }
      );
      if (!response.ok) throw new Error("Failed to send decision");
      setPendingDecision(null);
      localStorage.removeItem("pendingDecision");
    } catch (err) {
      setError(err.message);
    }
  };

  const renderDecisionUI = () => {
    if (!pendingDecision) return null;

    switch (pendingDecision.type) {
      case "buy_property":
        return (
          <div className="bg-white p-4 rounded-lg shadow mb-4">
            <h3 className="text-lg font-bold mb-2">Buy Property?</h3>
            <p>{pendingDecision.data.property}</p>
            <p>Price: ${pendingDecision.data.price}</p>
            <p>Your balance: ${pendingDecision.data.balance}</p>
            <div className="flex gap-2 mt-4">
              <Button onClick={() => handleDecision(true)}>Buy</Button>
              <Button onClick={() => handleDecision(false)}>Pass</Button>
            </div>
          </div>
        );

      case "upgrade_properties":
        return (
          <div className="bg-white p-4 rounded-lg shadow mb-4">
            <h3 className="text-lg font-bold mb-2">Upgrade Properties</h3>
            <p>Balance: ${pendingDecision.data.balance}</p>
            {Object.entries(pendingDecision.data.grouped_properties).map(
              ([group, properties]) => (
                <div key={group} className="mb-2">
                  <h4 className="font-medium">{group}</h4>
                  <ul className="list-disc pl-4">
                    {properties.map((prop, i) => (
                      <li key={i}>{prop}</li>
                    ))}
                  </ul>
                  <Button
                    onClick={() => handleDecision([group])}
                    className="mt-2"
                  >
                    Upgrade {group}
                  </Button>
                </div>
              )
            )}
            <Button onClick={() => handleDecision([])}>Skip Upgrades</Button>
          </div>
        );

      case "mortgage_properties":
        return (
          <div className="bg-white p-4 rounded-lg shadow mb-4">
            <h3 className="text-lg font-bold mb-2">Mortgage Properties</h3>
            <p>Balance: ${pendingDecision.data.balance}</p>
            <div className="space-y-2">
              {pendingDecision.data.properties.map((prop, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Button onClick={() => handleDecision([prop])}>
                    Mortgage {prop}
                  </Button>
                </div>
              ))}
            </div>
            <Button onClick={() => handleDecision([])} className="mt-4">
              Skip Mortgaging
            </Button>
          </div>
        );

      case "pay_jail_fine":
        return (
          <div className="bg-white p-4 rounded-lg shadow mb-4">
            <h3 className="text-lg font-bold mb-2">Pay Jail Fine?</h3>
            <p>Fine amount: ${pendingDecision.data.jail_fine}</p>
            <p>Your balance: ${pendingDecision.data.balance}</p>
            <div className="flex gap-2 mt-4">
              <Button onClick={() => handleDecision(true)}>Pay Fine</Button>
              <Button onClick={() => handleDecision(false)}>
                Stay in Jail
              </Button>
            </div>
          </div>
        );

      case "use_jail_card":
        return (
          <div className="bg-white p-4 rounded-lg shadow mb-4">
            <h3 className="text-lg font-bold mb-2">
              Use Get Out of Jail Free Card?
            </h3>
            <div className="flex gap-2 mt-4">
              <Button
                onClick={() => handleDecision(true)}
                disabled={!pendingDecision.data.has_card}
              >
                Use Card
              </Button>
              <Button onClick={() => handleDecision(false)}>
                Stay in Jail
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderPlayerCards = () => (
    <div className="space-y-4">
      {gameState && gameState.players.map((player, index) => (
        <PlayerCard
          key={index}
          player={player}
          isCurrentPlayer={index === gameState.currentPlayer}
        />
      ))}
    </div>
  );

  return (
    <div className="container mx-auto flex">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex-1 pr-2">
        <MonopolyBoard className="mb-4" />
      </div>

      <div className="w-1/3 pl-2 flex flex-col">
        {renderDecisionUI()}
        <div className="mt-4 w-full">{renderPlayerCards()}</div>
      </div>
    </div>
  );
};

export default HumanPlayerInterface;
