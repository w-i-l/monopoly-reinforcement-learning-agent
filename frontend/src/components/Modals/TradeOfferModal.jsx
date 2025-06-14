import React, { useState, useEffect, useRef } from "react";
import { X, Plus, Minus, DollarSign, Check } from "lucide-react";

// Glassmorphism styled card component with white theme
const GlassCard = ({ children, className = "", variant = "default" }) => {
  const variantStyles = {
    default: "bg-white/80 border-gray-200/50",
    success: "bg-white/80 border-green-200/50",
    warning: "bg-white/80 border-yellow-200/50",
  };

  return (
    <div
      className={`backdrop-blur-md rounded-xl border shadow-sm p-4 ${variantStyles[variant]} ${className}`}
    >
      {children}
    </div>
  );
};

// Styled button with glassmorphism effect
const GlassButton = ({
  children,
  onClick,
  variant = "default",
  disabled = false,
  className = "",
  icon = null,
}) => {
  const variantStyles = {
    default: "bg-blue-500 hover:bg-blue-600 text-white border-blue-400",
    success: "bg-green-500 hover:bg-green-600 text-white border-green-400",
    danger: "bg-red-500 hover:bg-red-600 text-white border-red-400",
    warning: "bg-yellow-500 hover:bg-yellow-600 text-white border-yellow-400",
    secondary: "bg-gray-200 hover:bg-gray-300 text-gray-700 border-gray-300",
    ghost:
      "bg-transparent hover:bg-gray-100 text-gray-700 border-transparent hover:border-gray-200",
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex items-center justify-center gap-2
        px-4 py-2 
        rounded-lg
        font-medium 
        transition-all
        border
        shadow-sm
        ${variantStyles[variant]}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        ${className}
      `}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

// Property item component
const PropertyItem = ({ property, selected, onToggle }) => {
  // Determine property group color
  const getPropertyColor = (name) => {
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
      utility: "#444444",
    };

    if (name.includes("Gara")) return colorMap.railway;
    if (name.includes("Uzina")) return colorMap.utility;
    if (name.includes("Rahova") || name.includes("Giulesti"))
      return colorMap.brown;
    if (
      name.includes("Vitan") ||
      name.includes("Pantelimon") ||
      name.includes("Berceni")
    )
      return colorMap.light_blue;
    if (
      name.includes("Titan") ||
      name.includes("Colentina") ||
      name.includes("Tei")
    )
      return colorMap.pink;
    if (
      name.includes("Timisoara") ||
      name.includes("Brasov") ||
      name.includes("Taberei")
    )
      return colorMap.orange;
    if (
      name.includes("Carol") ||
      name.includes("Kogalniceanu") ||
      name.includes("Eroilor")
    )
      return colorMap.red;
    if (
      name.includes("Titulescu") ||
      name.includes("Mai") ||
      name.includes("Dorobantilor")
    )
      return colorMap.yellow;
    if (
      name.includes("Unirii") ||
      name.includes("Cotroceni") ||
      name.includes("Victoriei")
    )
      return colorMap.green;
    if (name.includes("Magheru") || name.includes("Primaverii"))
      return colorMap.blue;

    return "#cccccc";
  };

  const color = getPropertyColor(property);

  return (
    <div
      className={`
        flex items-center justify-between
        px-3 py-2 my-1 
        rounded-lg cursor-pointer
        transition-all
        ${
          selected
            ? "bg-blue-50 border border-blue-200 shadow-sm"
            : "bg-gray-50 hover:bg-gray-100 border border-transparent"
        }
      `}
      onClick={onToggle}
    >
      <div className="flex items-center">
        <div
          className="w-4 h-4 rounded-full mr-2"
          style={{ backgroundColor: color }}
        />
        <span className="text-sm font-medium text-gray-700">{property}</span>
      </div>
      <div
        className={`
        w-5 h-5 flex items-center justify-center
        rounded-full transition-all
        ${
          selected
            ? "bg-blue-500 text-white"
            : "bg-white border border-gray-300 text-transparent"
        }
      `}
      >
        {selected && <Check size={12} />}
      </div>
    </div>
  );
};

// Form for a single trade offer
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
    <GlassCard className="mb-6">
      <div className="flex justify-between items-center mb-4 border-b border-gray-200 pb-3">
        <h3 className="text-lg font-bold text-gray-800">
          Trade Offer {index + 1}
        </h3>
        <GlassButton
          onClick={() => onRemove(index)}
          variant="danger"
          icon={<X size={16} />}
          className="px-2 py-1"
        >
          Remove
        </GlassButton>
      </div>

      <div className="mb-4">
        <label className="block mb-2 text-gray-700 font-medium">
          Trading with:
        </label>
        <select
          value={trade.target_player || ""}
          onChange={(e) => handleChange({ target_player: e.target.value })}
          className="w-full p-2 rounded-lg bg-gray-50 border border-gray-300 text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="" disabled>
            Select player...
          </option>
          {tradeData?.players.map((player, idx) => (
            <option key={idx} value={player.name}>
              {player.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Your Offer Section */}
        <div className="space-y-4">
          <h4 className="font-bold text-gray-800 text-md border-b border-gray-200 pb-1">
            Your Offer
          </h4>

          {/* Properties to offer */}
          <div>
            <label className="block text-sm text-gray-600 font-medium mb-2">
              Properties to offer:
            </label>
            <div className="max-h-48 overflow-y-auto pr-2 shadow-inner rounded-lg bg-gray-50 p-2">
              {tradeData?.my_data.properties.length > 0 ? (
                tradeData.my_data.properties.map((prop, idx) => (
                  <PropertyItem
                    key={idx}
                    property={prop}
                    selected={(trade.properties_offered || []).includes(prop)}
                    onToggle={() => toggleProperty(prop, "offered")}
                  />
                ))
              ) : (
                <div className="text-gray-500 text-sm italic p-2">
                  No properties to offer
                </div>
              )}
            </div>
          </div>

          {/* Money to offer */}
          <div>
            <label className="block text-sm text-gray-600 font-medium mb-2">
              Money to offer: (Max: {tradeData?.my_data.balance || 0}₩)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <div className="text-gray-400">₩</div>
              </div>
              <input
                type="number"
                value={trade.money_offered || 0}
                onChange={(e) =>
                  handleChange({ money_offered: parseInt(e.target.value) || 0 })
                }
                max={tradeData?.my_data.balance || 0}
                min={0}
                className="w-full pl-10 p-2 rounded-lg bg-gray-50 border border-gray-300 text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Jail cards to offer */}
          <div>
            <label className="block text-sm text-gray-600 font-medium mb-2">
              Jail Cards to offer: (Have: {tradeData?.my_data.jail_cards || 0})
            </label>
            <div className="flex items-center">
              <GlassButton
                onClick={() =>
                  handleChange({
                    jail_cards_offered: Math.max(
                      0,
                      (trade.jail_cards_offered || 0) - 1
                    ),
                  })
                }
                variant="secondary"
                icon={<Minus size={16} />}
                className="px-2"
                disabled={(trade.jail_cards_offered || 0) <= 0}
              />
              <span className="mx-3 px-3 py-1 rounded bg-gray-50 border border-gray-300 text-gray-800 min-w-8 text-center">
                {trade.jail_cards_offered || 0}
              </span>
              <GlassButton
                onClick={() =>
                  handleChange({
                    jail_cards_offered: Math.min(
                      tradeData?.my_data.jail_cards || 0,
                      (trade.jail_cards_offered || 0) + 1
                    ),
                  })
                }
                variant="secondary"
                icon={<Plus size={16} />}
                className="px-2"
                disabled={
                  (trade.jail_cards_offered || 0) >=
                  (tradeData?.my_data.jail_cards || 0)
                }
              />
            </div>
          </div>
        </div>

        {/* Request Section */}
        <div className="space-y-4">
          <h4 className="font-bold text-gray-800 text-md border-b border-gray-200 pb-1">
            Your Request
          </h4>

          {trade.target_player ? (
            <>
              {/* Properties to request */}
              <div>
                <label className="block text-sm text-gray-600 font-medium mb-2">
                  Properties to request:
                </label>
                <div className="max-h-48 overflow-y-auto pr-2 shadow-inner rounded-lg bg-gray-50 p-2">
                  {tradeData?.players.find(
                    (p) => p.name === trade.target_player
                  )?.properties.length > 0 ? (
                    tradeData?.players
                      .find((p) => p.name === trade.target_player)
                      ?.properties.map((prop, idx) => (
                        <PropertyItem
                          key={idx}
                          property={prop}
                          selected={(trade.properties_requested || []).includes(
                            prop
                          )}
                          onToggle={() => toggleProperty(prop, "requested")}
                        />
                      ))
                  ) : (
                    <div className="text-gray-500 text-sm italic p-2">
                      No properties to request
                    </div>
                  )}
                </div>
              </div>

              {/* Money to request */}
              <div>
                <label className="block text-sm text-gray-600 font-medium mb-2">
                  Money to request: (Max:
                  {tradeData?.players.find(
                    (p) => p.name === trade.target_player
                  )?.balance || 0}
                  ₩ )
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <div className="text-gray-400">₩</div>
                  </div>
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
                      )?.balance || 0
                    }
                    min={0}
                    className="w-full pl-10 p-2 rounded-lg bg-gray-50 border border-gray-300 text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Jail cards to request */}
              <div>
                <label className="block text-sm text-gray-600 font-medium mb-2">
                  Jail Cards to request: (They have:{" "}
                  {tradeData?.players.find(
                    (p) => p.name === trade.target_player
                  )?.jail_cards || 0}
                  )
                </label>
                <div className="flex items-center">
                  <GlassButton
                    onClick={() =>
                      handleChange({
                        jail_cards_requested: Math.max(
                          0,
                          (trade.jail_cards_requested || 0) - 1
                        ),
                      })
                    }
                    variant="secondary"
                    icon={<Minus size={16} />}
                    className="px-2"
                    disabled={(trade.jail_cards_requested || 0) <= 0}
                  />
                  <span className="mx-3 px-3 py-1 rounded bg-gray-50 border border-gray-300 text-gray-800 min-w-8 text-center">
                    {trade.jail_cards_requested || 0}
                  </span>
                  <GlassButton
                    onClick={() =>
                      handleChange({
                        jail_cards_requested: Math.min(
                          tradeData?.players.find(
                            (p) => p.name === trade.target_player
                          )?.jail_cards || 0,
                          (trade.jail_cards_requested || 0) + 1
                        ),
                      })
                    }
                    variant="secondary"
                    icon={<Plus size={16} />}
                    className="px-2"
                    disabled={
                      (trade.jail_cards_requested || 0) >=
                      (tradeData?.players.find(
                        (p) => p.name === trade.target_player
                      )?.jail_cards || 0)
                    }
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-gray-500">
                Please select a player to trade with
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Trade summary */}
      {trade.target_player && (
        <div className="mt-6 pt-3 border-t border-gray-200">
          <h4 className="font-bold text-gray-800 mb-2">Trade Summary</h4>
          <div className="grid grid-cols-2 gap-4 text-sm bg-gray-50 p-4 rounded-lg">
            <div>
              <p className="text-gray-600 font-medium mb-1">You offer:</p>
              <ul className="list-disc pl-5 text-gray-700">
                {(trade.properties_offered || []).map((prop, idx) => (
                  <li key={idx}>{prop}</li>
                ))}
                {trade.money_offered > 0 && <li>{trade.money_offered}₩</li>}
                {trade.jail_cards_offered > 0 && (
                  <li>
                    {trade.jail_cards_offered} Get Out of Jail Free card(s)
                  </li>
                )}
                {!trade.properties_offered?.length &&
                  !trade.money_offered &&
                  !trade.jail_cards_offered && (
                    <li className="text-gray-400 italic">Nothing</li>
                  )}
              </ul>
            </div>
            <div>
              <p className="text-gray-600 font-medium mb-1">You receive:</p>
              <ul className="list-disc pl-5 text-gray-700">
                {(trade.properties_requested || []).map((prop, idx) => (
                  <li key={idx}>{prop}</li>
                ))}
                {trade.money_requested > 0 && <li>{trade.money_requested}₩</li>}
                {trade.jail_cards_requested > 0 && (
                  <li>
                    {trade.jail_cards_requested} Get Out of Jail Free card(s)
                  </li>
                )}
                {!trade.properties_requested?.length &&
                  !trade.money_requested &&
                  !trade.jail_cards_requested && (
                    <li className="text-gray-400 italic">Nothing</li>
                  )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </GlassCard>
  );
};

// Main trade modal component - Create Trade Modal
export const CreateTradeModal = ({ isOpen, onClose, tradeData, onSubmit }) => {
  const [trades, setTrades] = useState([{}]);
  const [mounted, setMounted] = useState(false);
  const modalRef = useRef(null);

  // Reset trades when modal opens
  useEffect(() => {
    if (isOpen && !mounted) {
      // Prevent rendering issues by waiting for actual DOM to be ready
      const timer = setTimeout(() => {
        setMounted(true);
      }, 10);
      return () => clearTimeout(timer);
    } else if (!isOpen && mounted) {
      // Wait for animation to finish before unmounting
      const timer = setTimeout(() => {
        setMounted(false);
        setTrades([{}]); // Reset trades when modal closes
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen, mounted]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

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

  const handleCancel = () => {
    onClose();
    onSubmit([]);
  };

  const handleSubmit = () => {
    // Filter out empty and invalid trades
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

    onClose();
    onSubmit(validTrades);
  };

  const hasValidTrade = trades.some(
    (trade) =>
      trade.target_player &&
      ((trade.properties_offered && trade.properties_offered.length > 0) ||
        (trade.money_offered && trade.money_offered > 0) ||
        (trade.jail_cards_offered && trade.jail_cards_offered > 0) ||
        (trade.properties_requested && trade.properties_requested.length > 0) ||
        (trade.money_requested && trade.money_requested > 0) ||
        (trade.jail_cards_requested && trade.jail_cards_requested > 0))
  );

  return (
    <div
      className={`
      fixed inset-0 z-50 
      flex items-center justify-center 
      bg-black/50 backdrop-blur-sm
      transition-opacity duration-200
      ${mounted ? "opacity-100" : "opacity-0"}
    `}
    >
      {/* Modal content */}
      <div
        ref={modalRef}
        className={`
          relative w-full max-w-5xl mx-4 my-6 max-h-[90vh]
          bg-white rounded-xl shadow-lg
          transition-transform duration-300
          ${mounted ? "translate-y-0 scale-100" : "translate-y-8 scale-95"}
        `}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">
            Create Trade Offers
          </h2>
          <GlassButton
            onClick={onClose}
            variant="ghost"
            icon={<X size={20} />}
            className="rounded-full p-2"
          />
        </div>

        {/* Body - scrollable */}
        <div className="p-6 max-h-[calc(90vh-8rem)] overflow-y-auto">
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

          <GlassButton
            onClick={handleAddTrade}
            variant="success"
            icon={<Plus size={18} />}
            className="w-full mt-2"
          >
            Add Another Trade Offer
          </GlassButton>
        </div>

        {/* Footer */}
        <div className="px-6 py-0 border-t border-gray-200 flex justify-between" style={{padding: "20px"}}>
          <div className="flex gap-3">
            <GlassButton onClick={handleCancel} variant="secondary">
              Cancel
            </GlassButton>
          </div>
          <GlassButton
            onClick={handleSubmit}
            disabled={!hasValidTrade}
            variant="success"
            className={!hasValidTrade ? "opacity-50" : ""}
          >
            Submit Trade Offers
          </GlassButton>
        </div>
      </div>
    </div>
  );
};

// Component for reviewing trade offers
export const TradeOfferModal = ({
  isOpen,
  onClose,
  tradeOffer,
  onAccept,
  onReject,
}) => {
  const [mounted, setMounted] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    if (isOpen && !mounted) {
      // Prevent rendering issues by waiting for actual DOM to be ready
      const timer = setTimeout(() => {
        setMounted(true);
      }, 10);
      return () => clearTimeout(timer);
    } else if (!isOpen && mounted) {
      // Wait for animation to finish before unmounting
      const timer = setTimeout(() => {
        setMounted(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen, mounted]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !tradeOffer) return null;

  // Determine property group colors for visualization
  const getPropertyColor = (name) => {
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
      utility: "#444444",
    };

    if (name.includes("Gara")) return colorMap.railway;
    if (name.includes("Uzina")) return colorMap.utility;
    if (name.includes("Rahova") || name.includes("Giulesti"))
      return colorMap.brown;
    if (
      name.includes("Vitan") ||
      name.includes("Pantelimon") ||
      name.includes("Berceni")
    )
      return colorMap.light_blue;
    if (
      name.includes("Titan") ||
      name.includes("Colentina") ||
      name.includes("Tei")
    )
      return colorMap.pink;
    if (
      name.includes("Timisoara") ||
      name.includes("Brasov") ||
      name.includes("Taberei")
    )
      return colorMap.orange;
    if (
      name.includes("Carol") ||
      name.includes("Kogalniceanu") ||
      name.includes("Eroilor")
    )
      return colorMap.red;
    if (
      name.includes("Titulescu") ||
      name.includes("Mai") ||
      name.includes("Dorobantilor")
    )
      return colorMap.yellow;
    if (
      name.includes("Unirii") ||
      name.includes("Cotroceni") ||
      name.includes("Victoriei")
    )
      return colorMap.green;
    if (name.includes("Magheru") || name.includes("Primaverii"))
      return colorMap.blue;

    return "#cccccc";
  };

  return (
    <div
      className={`
      fixed inset-0 z-50 
      flex items-center justify-center 
      bg-black/50 backdrop-blur-sm
      transition-opacity duration-200
      ${mounted ? "opacity-100" : "opacity-0"}
    `}
    >
      {/* Modal content */}
      <div
        ref={modalRef}
        className={`
          relative w-full max-w-lg mx-4 
          bg-white rounded-xl shadow-lg
          transition-transform duration-300
          ${mounted ? "translate-y-0 scale-100" : "translate-y-8 scale-95"}
        `}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">
            Trade Offer from {tradeOffer.source_player}
          </h2>
          <GlassButton
            onClick={onClose}
            variant="ghost"
            icon={<X size={18} />}
            className="rounded-full p-2"
          />
        </div>

        {/* Body */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* What you receive */}
            <GlassCard
              className="border-green-200/50 bg-green-50/50"
              variant="success"
            >
              <h3 className="font-bold text-gray-800 mb-4 pb-2 border-b border-green-200/50">
                You Will Receive:
              </h3>
              <div className="space-y-2">
                {/* Properties */}
                {tradeOffer.properties_offered &&
                tradeOffer.properties_offered.length > 0 ? (
                  <div className="mb-4">
                    <h4 className="text-gray-600 text-sm mb-2">Properties:</h4>
                    <div className="space-y-1">
                      {tradeOffer.properties_offered.map((prop, idx) => (
                        <div
                          key={idx}
                          className="flex items-center text-gray-700 p-1 bg-white/80 rounded border border-gray-200/50"
                        >
                          <div
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: getPropertyColor(prop) }}
                          />
                          <span>{prop}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* Money */}
                {tradeOffer.money_offered > 0 && (
                  <div className="mb-4">
                    <h4 className="text-gray-600 text-sm mb-2">Money:</h4>
                    <div className="flex items-center text-gray-700 p-2 bg-white/80 rounded border border-gray-200/50">
                      <DollarSign size={16} className="mr-1 text-green-600" />
                      <span className="font-semibold">
                        {tradeOffer.money_offered}
                      </span>
                    </div>
                  </div>
                )}

                {/* Jail Cards */}
                {tradeOffer.jail_cards_offered > 0 && (
                  <div>
                    <h4 className="text-gray-600 text-sm mb-2">Jail Cards:</h4>
                    <div className="flex items-center text-gray-700 p-2 bg-white/80 rounded border border-gray-200/50">
                      <span className="font-semibold mr-1">
                        {tradeOffer.jail_cards_offered}
                      </span>
                      <span>Get Out of Jail Free card(s)</span>
                    </div>
                  </div>
                )}

                {/* Nothing to receive */}
                {!tradeOffer.properties_offered?.length &&
                  !tradeOffer.money_offered &&
                  !tradeOffer.jail_cards_offered && (
                    <div className="text-gray-500 italic text-center py-6 bg-white/80 rounded border border-gray-200/50">
                      Nothing to receive
                    </div>
                  )}
              </div>
            </GlassCard>

            {/* What you give */}
            <GlassCard
              className="border-red-200/50 bg-red-50/50"
              variant="warning"
            >
              <h3 className="font-bold text-gray-800 mb-4 pb-2 border-b border-red-200/50">
                In Exchange For:
              </h3>
              <div className="space-y-2">
                {/* Properties */}
                {tradeOffer.properties_requested &&
                tradeOffer.properties_requested.length > 0 ? (
                  <div className="mb-4">
                    <h4 className="text-gray-600 text-sm mb-2">Properties:</h4>
                    <div className="space-y-1">
                      {tradeOffer.properties_requested.map((prop, idx) => (
                        <div
                          key={idx}
                          className="flex items-center text-gray-700 p-1 bg-white/80 rounded border border-gray-200/50"
                        >
                          <div
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: getPropertyColor(prop) }}
                          />
                          <span>{prop}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* Money */}
                {tradeOffer.money_requested > 0 && (
                  <div className="mb-4">
                    <h4 className="text-gray-600 text-sm mb-2">Money:</h4>
                    <div className="flex items-center text-gray-700 p-2 bg-white/80 rounded border border-gray-200/50">
                      <DollarSign size={16} className="mr-1 text-red-600" />
                      <span className="font-semibold">
                        {tradeOffer.money_requested}
                      </span>
                    </div>
                  </div>
                )}

                {/* Jail Cards */}
                {tradeOffer.jail_cards_requested > 0 && (
                  <div>
                    <h4 className="text-gray-600 text-sm mb-2">Jail Cards:</h4>
                    <div className="flex items-center text-gray-700 p-2 bg-white/80 rounded border border-gray-200/50">
                      <span className="font-semibold mr-1">
                        {tradeOffer.jail_cards_requested}
                      </span>
                      <span>Get Out of Jail Free card(s)</span>
                    </div>
                  </div>
                )}

                {/* Nothing to give */}
                {!tradeOffer.properties_requested?.length &&
                  !tradeOffer.money_requested &&
                  !tradeOffer.jail_cards_requested && (
                    <div className="text-gray-500 italic text-center py-6 bg-white/80 rounded border border-gray-200/50">
                      Nothing to give
                    </div>
                  )}
              </div>
            </GlassCard>
          </div>

          {/* Trade evaluation */}
          <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg shadow-sm">
            <h3 className="font-bold text-gray-800 mb-2">Trade Evaluation</h3>
            <p className="text-gray-600 text-sm">
              Consider if this trade benefits your overall strategy. Look at
              property sets, cash flow, and game position.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <GlassButton onClick={onReject} variant="danger">
            Reject Offer
          </GlassButton>
          <GlassButton onClick={onAccept} variant="success">
            Accept Offer
          </GlassButton>
        </div>
      </div>
    </div>
  );
};

// Export the enhanced trade modal components
export default { CreateTradeModal, TradeOfferModal };
