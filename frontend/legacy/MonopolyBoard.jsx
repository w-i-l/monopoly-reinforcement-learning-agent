import React, { useState, useEffect } from "react";
import { Dice1, Dice2, Dice3, Dice4, Dice5, Dice6 } from "lucide-react";
import BOARD_PROPERTIES from "./constants/boardProperties";
import Modal from "react-modal";

const DiceIcon = ({ value }) => {
  const icons = {
    1: Dice1,
    2: Dice2,
    3: Dice3,
    4: Dice4,
    5: Dice5,
    6: Dice6,
  };
  const DiceComponent = icons[value];
  return <DiceComponent className="w-12 h-12" />;
};

const PlayerCard = ({ player, isCurrentPlayer }) => (
  <div
    className={`p-4 rounded-lg shadow-md mb-4 ${
      isCurrentPlayer ? "bg-blue-50" : "bg-white"
    }`}
  >
    <h3 className="text-lg font-bold mb-2">{player.name}</h3>
    <div className="flex flex-col gap-2">
      <p>Balance: {player.balance}₩</p>
      <div className="text-sm">
        <p>Properties:</p>
        <ul className="list-disc pl-4">
          {player.properties.map((prop) => (
            <li key={prop.id}>{prop.name}</li>
          ))}
        </ul>
      </div>
      {player.houses && Object.keys(player.houses).length > 0 && (
        <div>
          <p>Houses:</p>
          <ul className="list-disc pl-4">
            {Object.entries(player.houses).map(([property, count]) => (
              <li key={property}>{`${property}: ${count}`}</li>
            ))}
          </ul>
        </div>
      )}
      {player.hotels && Object.keys(player.hotels).length > 0 && (
        <div>
          <p>Hotels:</p>
          <ul className="list-disc pl-4">
            {Object.entries(player.hotels).map(([property, count]) => (
              <li key={property}>{`${property}: ${count}`}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  </div>
);

const MortgagePropertyModal = ({
  isOpen,
  onRequestClose,
  properties,
  onSelectProperty,
}) => {
  const [selectedProperty, setSelectedProperty] = useState("");

  const handleSelect = () => {
    onSelectProperty(selectedProperty);
    onRequestClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      contentLabel="Select Property"
      className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto mt-20"
      overlayClassName="fixed inset-0 bg-black bg-opacity-50"
    >
      <h2 className="text-xl font-bold mb-4 text-black">
        Select a Property to Mortgage
      </h2>
      <select
        value={selectedProperty}
        onChange={(e) => setSelectedProperty(e.target.value)}
        className="w-full p-2 border rounded mb-4 text-white"
      >
        <option value="" disabled>
          Select a property
        </option>
        {properties.map((property) => (
          <option key={property.id} value={property.name}>
            {property.name}
          </option>
        ))}
      </select>
      <div className="flex justify-end gap-2">
        <button
          onClick={onRequestClose}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 text-white"
        >
          Cancel
        </button>
        <button
          onClick={handleSelect}
          disabled={!selectedProperty}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          Mortgage Property
        </button>
      </div>
    </Modal>
  );
};

const MonopolyBoard = () => {
  const [gameState, setGameState] = useState(null);
  const [lastRoll, setLastRoll] = useState(null);
  const [isRolling, setIsRolling] = useState(false);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const API_BASE_URL = "http://127.0.0.1:5000";

  const fetchGameState = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/game-state`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setGameState(data);
      setError(null);
    } catch (error) {
      console.error("Error fetching game state:", error);
      setError(`Connection error: ${error.message}`);
      setGameState(null);
    }
  };

  const actions = {
    rollDice: async () => {
      setIsRolling(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/roll-dice`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (!response.ok)
          throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        setLastRoll(data);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      } finally {
        setIsRolling(false);
      }
    },

    buyProperty: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/buy-property`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (!response.ok)
          throw new Error(`HTTP error! status: ${response.status}`);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },

    endTurn: async () => {
      try {
        await fetch(`${API_BASE_URL}/api/end-turn`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        setLastRoll(null);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },

    payRent: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/pay-rent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (!response.ok)
          throw new Error(`HTTP error! status: ${response.status}`);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },

    mortgageProperty: async (propertyName) => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/mortgage-property`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ property_name: propertyName }),
        });
        if (!response.ok)
          throw new Error(`HTTP error! status: ${response.status}`);
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },

    placeHouse: async (propertyName) => {
      try {
        const body = { property_name: propertyName };
        const response = await fetch(`${API_BASE_URL}/api/place-house`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `HTTP error! status: ${response.status}`
          );
        }
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },
    placeHotel: async (propertyName) => {
      try {
        const body = { property_name: propertyName };
        const response = await fetch(`${API_BASE_URL}/api/place-hotel`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `HTTP error! status: ${response.status}`
          );
        }
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },
    sellHouse: async (propertyName) => {
      try {
        const body = { property_name: propertyName };
        const response = await fetch(`${API_BASE_URL}/api/sell-house`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `HTTP error! status: ${response.status}`
          );
        }
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },
    sellHotel: async (propertyName) => {
      try {
        const body = { property_name: propertyName };
        const response = await fetch(`${API_BASE_URL}/api/sell-hotel`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `HTTP error! status: ${response.status}`
          );
        }
        await fetchGameState();
      } catch (error) {
        setError(error.message);
      }
    },
  };

  useEffect(() => {
    fetchGameState();
  }, []);

  const renderSquare = (property, index) => {
    const players = gameState?.players || [];
    const playersHere = players.filter((p) => p.position === index);
    const playersColors = ["red", "blue", "green", "purple"];
    const isOwned = gameState.ownedProperties.includes(property.id);
    const isMortgaged = gameState.mortgagedProperties.includes(property.id);

    return (
      <div
        key={index}
        className="w-20 h-20 border border-black flex flex-col items-center justify-center relative"
        style={{
          backgroundColor: property.color,
          color: "white",
          opacity: isMortgaged ? 0.5 : 1,
        }}
      >
        <span className="text-xs text-center">{property.name}</span>
        {isOwned && (
          <div className="absolute top-0 right-0 w-3 h-3 bg-yellow-400 rounded-full" />
        )}
        {playersHere.map((player, i) => (
          <div
            key={i}
            className="absolute w-4 h-4 rounded-full"
            style={{
              backgroundColor: playersColors[i % 4],
              top: `${i * 20 + 5}%`,
              right: "5%",
              padding: "10px",
            }}
          >
            <span className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white text-xs font-bold">
              {player.name.split(" ").pop()}
            </span>
          </div>
        ))}
      </div>
    );
  };

  if (error) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
        Error: {error}
      </div>
    );
  }

  if (!gameState) {
    return <div className="p-4 text-center">Loading game state...</div>;
  }

  const currentPlayer = gameState.players[gameState.currentPlayer];

  return (
    <div className="flex gap-4 p-4">
      <div className="flex flex-col">
        <div className="board">
          {[0, 10, 20, 30].map((start) => (
            <div key={start} className="flex">
              {BOARD_PROPERTIES.slice(start, start + 10).map(
                (property, index) => renderSquare(property, index + start)
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-4 w-80">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4">
            Current Turn: {currentPlayer.name}
          </h2>
          <div className="flex flex-col gap-2">
            <p>Balance: {currentPlayer.balance}₩</p>
            {lastRoll && (
              <div className="flex items-center gap-2">
                <DiceIcon value={lastRoll.dice[0]} />
                <DiceIcon value={lastRoll.dice[1]} />
              </div>
            )}
            <div className="flex flex-col gap-2">
              <button
                className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-blue-600"
                onClick={actions.rollDice}
                disabled={isRolling || lastRoll}
              >
                Roll Dice
              </button>
              <button
                className="bg-green-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-green-600"
                onClick={actions.buyProperty}
              >
                Buy Property
              </button>
              <button
                className="bg-red-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-red-600"
                onClick={actions.payRent}
                disabled={!lastRoll}
              >
                Pay Rent
              </button>
              <button
                className="bg-yellow-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-yellow-600"
                onClick={() => setIsModalOpen(true)}
                disabled={!currentPlayer.properties.length}
              >
                Mortgage Property
              </button>
              <button
                className="bg-gray-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-gray-600"
                onClick={actions.endTurn}
                disabled={!lastRoll}
              >
                End Turn
              </button>
              <button
                className="bg-gray-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-gray-600"
                onClick={() => actions.placeHouse("Rahova (brown)")}
                disabled={!lastRoll}
              >
                Buy House
              </button>
              <button
                className="bg-gray-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-gray-600"
                onClick={() => actions.placeHotel("Rahova (brown)")}
                disabled={!lastRoll}
              >
                Buy Hotel
              </button>
              <button
                className="bg-gray-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-gray-600"
                onClick={() => actions.sellHouse("Rahova (brown)")}
                disabled={!lastRoll}
              >
                Sell House
              </button>
              <button
                className="bg-gray-500 text-white px-4 py-2 rounded disabled:opacity-50 hover:bg-gray-600"
                onClick={() => actions.sellHotel("Rahova (brown)")}
                disabled={!lastRoll}
              >
                Sell Hotel
              </button>
            </div>
          </div>
        </div>

        {gameState.players.map((player, index) => (
          <PlayerCard
            key={index}
            player={player}
            isCurrentPlayer={index === gameState.currentPlayer}
          />
        ))}

        <MortgagePropertyModal
          isOpen={isModalOpen}
          onRequestClose={() => setIsModalOpen(false)}
          properties={currentPlayer.properties}
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
