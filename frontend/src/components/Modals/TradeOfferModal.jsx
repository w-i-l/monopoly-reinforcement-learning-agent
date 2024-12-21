import React, { useState } from "react";
import Button from "../UI/Button";

const TradeForm = ({ tradeData, onRemove, onChange, trade, index }) => {
  const handleChange = (changes) => {
    onChange(index, { ...trade, ...changes });
  };

  const toggleProperty = (property, type) => {
    const key =
      type === "offered" ? "properties_offered" : "properties_requested";
    const currentProps = trade[key] || [];
    const newProps = currentProps.includes(property)
      ? currentProps.filter((p) => p !== property)
      : [...currentProps, property];
    handleChange({ [key]: newProps });
  };

  return (
    <div className="border rounded-lg p-4 mb-4">
      <div className="flex justify-between mb-4">
        <h3 className="text-lg font-semibold">Trade {index + 1}</h3>
        <Button
          onClick={() => onRemove(index)}
          className="bg-red-500 hover:bg-red-600"
        >
          Remove Trade
        </Button>
      </div>

      <div className="mb-4">
        <label className="block mb-2">Trade with:</label>
        <select
          value={trade.target_player || ""}
          onChange={(e) => handleChange({ target_player: e.target.value })}
          className="w-full p-2 border rounded text-white"
        >
          <option value="">Select player...</option>
          {tradeData?.players.map((player, idx) => (
            <option key={idx} value={player.name}>
              {player.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="font-semibold mb-2">Your Offer:</h4>
          <div className="space-y-2">
            <div className="mb-4">
              <label className="block text-sm mb-1">Properties:</label>
              {tradeData?.my_data.properties.map((prop, idx) => (
                <div key={idx} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={(trade.properties_offered || []).includes(prop)}
                    onChange={() => toggleProperty(prop, "offered")}
                    className="mr-2"
                  />
                  <span>{prop}</span>
                </div>
              ))}
            </div>
            <div className="mb-4">
              <label className="block text-sm mb-1">
                Money (max: ${tradeData?.my_data.balance}):
              </label>
              <input
                type="number"
                value={trade.money_offered || 0}
                onChange={(e) =>
                  handleChange({ money_offered: parseInt(e.target.value) || 0 })
                }
                max={tradeData?.my_data.balance}
                min={0}
                className="w-full p-2 border rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm mb-1">
                Jail Cards (have: {tradeData?.my_data.jail_cards}):
              </label>
              <input
                type="number"
                value={trade.jail_cards_offered || 0}
                onChange={(e) =>
                  handleChange({
                    jail_cards_offered: parseInt(e.target.value) || 0,
                  })
                }
                max={tradeData?.my_data.jail_cards}
                min={0}
                className="w-full p-2 border rounded text-white"
              />
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-semibold mb-2">Request in Return:</h4>
          {trade.target_player && (
            <div className="space-y-2">
              <div className="mb-4">
                <label className="block text-sm mb-1">Properties:</label>
                {tradeData?.players
                  .find((p) => p.name === trade.target_player)
                  ?.properties.map((prop, idx) => (
                    <div key={idx} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(trade.properties_requested || []).includes(
                          prop
                        )}
                        onChange={() => toggleProperty(prop, "requested")}
                        className="mr-2"
                      />
                      <span>{prop}</span>
                    </div>
                  ))}
              </div>
              <div className="mb-4">
                <label className="block text-sm mb-1">
                  Money (max: $
                  {
                    tradeData?.players.find(
                      (p) => p.name === trade.target_player
                    )?.balance
                  }
                  ):
                </label>
                <input
                  type="number"
                  value={trade.money_requested || 0}
                  onChange={(e) =>
                    handleChange({
                      money_requested: parseInt(e.target.value) || 0,
                    })
                  }
                  max={
                    tradeData?.players.find(
                      (p) => p.name === trade.target_player
                    )?.balance
                  }
                  min={0}
                  className="w-full p-2 border rounded text-white"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">
                  Jail Cards (max:{" "}
                  {
                    tradeData?.players.find(
                      (p) => p.name === trade.target_player
                    )?.jail_cards
                  }
                  ):
                </label>
                <input
                  type="number"
                  value={trade.jail_cards_requested || 0}
                  onChange={(e) =>
                    handleChange({
                      jail_cards_requested: parseInt(e.target.value) || 0,
                    })
                  }
                  max={
                    tradeData?.players.find(
                      (p) => p.name === trade.target_player
                    )?.jail_cards
                  }
                  min={0}
                  className="w-full p-2 border rounded text-white"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const CreateTradeModal = ({ isOpen, onClose, tradeData, onSubmit }) => {
  const [trades, setTrades] = useState([{}]);

  if (!isOpen || !tradeData) return null;

  const handleTradeChange = (index, updatedTrade) => {
    const newTrades = [...trades];
    newTrades[index] = updatedTrade;
    setTrades(newTrades);
  };

  const handleRemoveTrade = (index) => {
    if (trades.length > 1) {
      setTrades(trades.filter((_, i) => i !== index));
    }
  };

  const handleAddTrade = () => {
    setTrades([...trades, {}]);
  };

  const handleSubmit = () => {
    // Filter out empty trades and submit
    const validTrades = trades.filter(
      (trade) =>
        trade.target_player &&
        ((trade.properties_offered && trade.properties_offered.length > 0) ||
          (trade.money_offered && trade.money_offered > 0) ||
          (trade.jail_cards_offered && trade.jail_cards_offered > 0) ||
          (trade.properties_requested &&
            trade.properties_requested.length > 0) ||
          (trade.money_requested && trade.money_requested > 0) ||
          (trade.jail_cards_requested && trade.jail_cards_requested > 0))
    );

    if (validTrades.length > 0) {
      onSubmit(validTrades);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center overflow-auto">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-4xl mx-auto my-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Create Trade Offers</h2>
          <Button
            onClick={handleAddTrade}
            className="bg-green-500 hover:bg-green-600"
          >
            Add Another Trade
          </Button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto">
          {trades.map((trade, index) => (
            <TradeForm
              key={index}
              index={index}
              trade={trade}
              tradeData={tradeData}
              onChange={handleTradeChange}
              onRemove={handleRemoveTrade}
            />
          ))}
        </div>

        <div className="flex justify-end gap-2 mt-4">
          <Button onClick={onClose} className="bg-gray-500 hover:bg-gray-600">
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!trades.some((t) => t.target_player)}
            className="bg-blue-500 hover:bg-blue-600"
          >
            Submit Trade Offers
          </Button>
        </div>
      </div>
    </div>
  );
};

export const TradeOfferModal = ({
  isOpen,
  onClose,
  tradeOffer,
  onAccept,
  onReject,
}) => {
  if (!isOpen || !tradeOffer) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
        <h2 className="text-xl font-bold mb-4">
          Trade Offer from {tradeOffer.source_player}
        </h2>

        <div className="mb-4">
          <h3 className="font-semibold mb-2">You Will Receive:</h3>
          <ul className="list-disc pl-4">
            {tradeOffer.properties_offered?.map((prop, idx) => (
              <li key={idx}>{prop}</li>
            ))}
            {tradeOffer.money_offered > 0 && (
              <li>${tradeOffer.money_offered}</li>
            )}
            {tradeOffer.jail_cards_offered > 0 && (
              <li>
                {tradeOffer.jail_cards_offered} Get Out of Jail Free card(s)
              </li>
            )}
          </ul>
        </div>

        <div className="mb-6">
          <h3 className="font-semibold mb-2">In Exchange For:</h3>
          <ul className="list-disc pl-4">
            {tradeOffer.properties_requested?.map((prop, idx) => (
              <li key={idx}>{prop}</li>
            ))}
            {tradeOffer.money_requested > 0 && (
              <li>${tradeOffer.money_requested}</li>
            )}
            {tradeOffer.jail_cards_requested > 0 && (
              <li>
                {tradeOffer.jail_cards_requested} Get Out of Jail Free card(s)
              </li>
            )}
          </ul>
        </div>

        <div className="flex justify-end gap-2">
          <Button onClick={onReject} className="bg-red-500 hover:bg-red-600">
            Reject
          </Button>
          <Button
            onClick={onAccept}
            className="bg-green-500 hover:bg-green-600"
          >
            Accept
          </Button>
        </div>
      </div>
    </div>
  );
};
