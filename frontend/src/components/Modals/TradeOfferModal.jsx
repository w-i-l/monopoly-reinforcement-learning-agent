import React, { useState, useEffect } from "react";
import { X, Plus, Minus, DollarSign, Check } from "lucide-react";

// Glassmorphism styled card component
const GlassCard = ({ children, className = "" }) => (
  <div className={`bg-white bg-opacity-20 backdrop-blur-lg rounded-xl border border-white border-opacity-20 shadow-lg p-4 ${className}`}>
    {children}
  </div>
);

// Styled button with glassmorphism effect
const GlassButton = ({ 
  children, 
  onClick, 
  variant = "default", 
  disabled = false,
  className = "",
  icon = null
}) => {
  const variantStyles = {
    default: "bg-blue-500 bg-opacity-80 hover:bg-blue-600 text-white",
    success: "bg-green-500 bg-opacity-80 hover:bg-green-600 text-white",
    danger: "bg-red-500 bg-opacity-80 hover:bg-red-600 text-white",
    warning: "bg-yellow-500 bg-opacity-80 hover:bg-yellow-600 text-white",
    secondary: "bg-gray-500 bg-opacity-80 hover:bg-gray-600 text-white",
    ghost: "bg-transparent hover:bg-white hover:bg-opacity-20 text-gray-200"
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
        backdrop-blur-sm
        ${variantStyles[variant]}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        ${className}
      `}
    >
      {icon && <span>{icon}</span>}
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
      utility: "#444444"
    };

    if (name.includes("Gara")) return colorMap.railway;
    if (name.includes("Uzina")) return colorMap.utility;
    if (name.includes("Rahova") || name.includes("Giulesti")) return colorMap.brown;
    if (name.includes("Vitan") || name.includes("Pantelimon") || name.includes("Berceni")) return colorMap.light_blue;
    if (name.includes("Titan") || name.includes("Colentina") || name.includes("Tei")) return colorMap.pink;
    if (name.includes("Timisoara") || name.includes("Brasov") || name.includes("Taberei")) return colorMap.orange;
    if (name.includes("Carol") || name.includes("Kogalniceanu") || name.includes("Eroilor")) return colorMap.red;
    if (name.includes("Titulescu") || name.includes("Mai") || name.includes("Dorobantilor")) return colorMap.yellow;
    if (name.includes("Unirii") || name.includes("Cotroceni") || name.includes("Victoriei")) return colorMap.green;
    if (name.includes("Magheru") || name.includes("Primaverii")) return colorMap.blue;
    
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
        ${selected ? 'bg-white bg-opacity-30 shadow-md' : 'bg-white bg-opacity-10 hover:bg-opacity-20'}
      `}
      onClick={onToggle}
    >
      <div className="flex items-center">
        <div 
          className="w-4 h-4 rounded-full mr-2" 
          style={{ backgroundColor: color }}
        />
        <span className="text-sm font-medium">{property}</span>
      </div>
      <div className={`
        w-5 h-5 flex items-center justify-center
        rounded-full transition-all
        ${selected 
          ? 'bg-blue-500 text-white' 
          : 'bg-white bg-opacity-20 text-transparent'}
      `}>
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
    const key = type === "offered" ? "properties_offered" : "properties_requested";
    const currentProps = trade[key] || [];
    const newProps = currentProps.includes(property)
      ? currentProps.filter((p) => p !== property)
      : [...currentProps, property];
    handleChange({ [key]: newProps });
  };

  return (
    <GlassCard className="mb-6 overflow-hidden">
      <div className="flex justify-between items-center mb-4 border-b border-white border-opacity-20 pb-3">
        <h3 className="text-lg font-bold text-white">Trade Offer {index + 1}</h3>
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
        <label className="block mb-2 text-white font-medium">Trading with:</label>
        <select
          value={trade.target_player || ""}
          onChange={(e) => handleChange({ target_player: e.target.value })}
          className="w-full p-2 rounded-lg bg-white bg-opacity-20 backdrop-blur-sm border border-white border-opacity-20 text-white"
        >
          <option value="" disabled>Select player...</option>
          {tradeData?.players.map((player, idx) => (
            <option key={idx} value={player.name} className="bg-gray-800">
              {player.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Your Offer Section */}
        <div className="space-y-4">
          <h4 className="font-bold text-white text-md border-b border-white border-opacity-20 pb-1">
            Your Offer
          </h4>

          {/* Properties to offer */}
          <div>
            <label className="block text-sm text-white font-medium mb-2">Properties to offer:</label>
            <div className="max-h-48 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white scrollbar-thumb-opacity-20 scrollbar-track-transparent">
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
                <div className="text-white text-opacity-60 text-sm italic">No properties to offer</div>
              )}
            </div>
          </div>

          {/* Money to offer */}
          <div>
            <label className="block text-sm text-white font-medium mb-2">
              Money to offer: (Max: ${tradeData?.my_data.balance || 0})
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <DollarSign size={16} className="text-white text-opacity-60" />
              </div>
              <input
                type="number"
                value={trade.money_offered || 0}
                onChange={(e) => handleChange({ money_offered: parseInt(e.target.value) || 0 })}
                max={tradeData?.my_data.balance || 0}
                min={0}
                className="w-full pl-10 p-2 rounded-lg bg-white bg-opacity-20 backdrop-blur-sm border border-white border-opacity-20 text-white"
              />
            </div>
          </div>

          {/* Jail cards to offer */}
          <div>
            <label className="block text-sm text-white font-medium mb-2">
              Jail Cards to offer: (Have: {tradeData?.my_data.jail_cards || 0})
            </label>
            <div className="flex items-center">
              <GlassButton
                onClick={() => handleChange({ 
                  jail_cards_offered: Math.max(0, (trade.jail_cards_offered || 0) - 1) 
                })}
                variant="ghost"
                icon={<Minus size={16} />}
                className="px-2"
                disabled={(trade.jail_cards_offered || 0) <= 0}
              />
              <span className="mx-3 px-3 py-1 rounded bg-white bg-opacity-20 text-white min-w-8 text-center">
                {trade.jail_cards_offered || 0}
              </span>
              <GlassButton
                onClick={() => handleChange({ 
                  jail_cards_offered: Math.min(tradeData?.my_data.jail_cards || 0, (trade.jail_cards_offered || 0) + 1) 
                })}
                variant="ghost"
                icon={<Plus size={16} />}
                className="px-2"
                disabled={(trade.jail_cards_offered || 0) >= (tradeData?.my_data.jail_cards || 0)}
              />
            </div>
          </div>
        </div>

        {/* Request Section */}
        <div className="space-y-4">
          <h4 className="font-bold text-white text-md border-b border-white border-opacity-20 pb-1">
            Your Request
          </h4>

          {trade.target_player ? (
            <>
              {/* Properties to request */}
              <div>
                <label className="block text-sm text-white font-medium mb-2">Properties to request:</label>
                <div className="max-h-48 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white scrollbar-thumb-opacity-20 scrollbar-track-transparent">
                  {tradeData?.players.find(p => p.name === trade.target_player)?.properties.length > 0 ? (
                    tradeData?.players
                      .find(p => p.name === trade.target_player)
                      ?.properties.map((prop, idx) => (
                        <PropertyItem
                          key={idx}
                          property={prop}
                          selected={(trade.properties_requested || []).includes(prop)}
                          onToggle={() => toggleProperty(prop, "requested")}
                        />
                      ))
                  ) : (
                    <div className="text-white text-opacity-60 text-sm italic">No properties to request</div>
                  )}
                </div>
              </div>

              {/* Money to request */}
              <div>
                <label className="block text-sm text-white font-medium mb-2">
                  Money to request: (Max: ${tradeData?.players.find(p => p.name === trade.target_player)?.balance || 0})
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <DollarSign size={16} className="text-white text-opacity-60" />
                  </div>
                  <input
                    type="number"
                    value={trade.money_requested || 0}
                    onChange={(e) => handleChange({ money_requested: parseInt(e.target.value) || 0 })}
                    max={tradeData?.players.find(p => p.name === trade.target_player)?.balance || 0}
                    min={0}
                    className="w-full pl-10 p-2 rounded-lg bg-white bg-opacity-20 backdrop-blur-sm border border-white border-opacity-20 text-white"
                  />
                </div>
              </div>

              {/* Jail cards to request */}
              <div>
                <label className="block text-sm text-white font-medium mb-2">
                  Jail Cards to request: (They have: {tradeData?.players.find(p => p.name === trade.target_player)?.jail_cards || 0})
                </label>
                <div className="flex items-center">
                  <GlassButton
                    onClick={() => handleChange({ 
                      jail_cards_requested: Math.max(0, (trade.jail_cards_requested || 0) - 1) 
                    })}
                    variant="ghost"
                    icon={<Minus size={16} />}
                    className="px-2"
                    disabled={(trade.jail_cards_requested || 0) <= 0}
                  />
                  <span className="mx-3 px-3 py-1 rounded bg-white bg-opacity-20 text-white min-w-8 text-center">
                    {trade.jail_cards_requested || 0}
                  </span>
                  <GlassButton
                    onClick={() => handleChange({ 
                      jail_cards_requested: Math.min(
                        tradeData?.players.find(p => p.name === trade.target_player)?.jail_cards || 0, 
                        (trade.jail_cards_requested || 0) + 1
                      ) 
                    })}
                    variant="ghost"
                    icon={<Plus size={16} />}
                    className="px-2"
                    disabled={(trade.jail_cards_requested || 0) >= (tradeData?.players.find(p => p.name === trade.target_player)?.jail_cards || 0)}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-white text-opacity-60">
              Please select a player to trade with
            </div>
          )}
        </div>
      </div>
      
      {/* Trade summary */}
      {trade.target_player && (
        <div className="mt-6 pt-3 border-t border-white border-opacity-20">
          <h4 className="font-bold text-white mb-2">Trade Summary</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-white text-opacity-80">You offer:</p>
              <ul className="list-disc pl-5 text-white">
                {(trade.properties_offered || []).map((prop, idx) => (
                  <li key={idx}>{prop}</li>
                ))}
                {(trade.money_offered > 0) && <li>${trade.money_offered}</li>}
                {(trade.jail_cards_offered > 0) && <li>{trade.jail_cards_offered} Get Out of Jail Free card(s)</li>}
                {!trade.properties_offered?.length && !trade.money_offered && !trade.jail_cards_offered && 
                  <li className="text-white text-opacity-50 italic">Nothing</li>
                }
              </ul>
            </div>
            <div>
              <p className="text-white text-opacity-80">You receive:</p>
              <ul className="list-disc pl-5 text-white">
                {(trade.properties_requested || []).map((prop, idx) => (
                  <li key={idx}>{prop}</li>
                ))}
                {(trade.money_requested > 0) && <li>${trade.money_requested}</li>}
                {(trade.jail_cards_requested > 0) && <li>{trade.jail_cards_requested} Get Out of Jail Free card(s)</li>}
                {!trade.properties_requested?.length && !trade.money_requested && !trade.jail_cards_requested && 
                  <li className="text-white text-opacity-50 italic">Nothing</li>
                }
              </ul>
            </div>
          </div>
        </div>
      )}
    </GlassCard>
  );
};

// Main trade modal component
export const CreateTradeModal = ({ isOpen, onClose, tradeData, onSubmit }) => {
  const [trades, setTrades] = useState([{}]);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Reset trades when modal opens
  useEffect(() => {
    if (isOpen) {
      setIsTransitioning(true);
      setTimeout(() => {
        setIsTransitioning(false);
      }, 300);
    }
  }, [isOpen]);

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
          (trade.properties_requested && trade.properties_requested.length > 0) ||
          (trade.money_requested && trade.money_requested > 0) ||
          (trade.jail_cards_requested && trade.jail_cards_requested > 0))
    );

    onSubmit(validTrades);
  };

  const hasValidTrade = trades.some(trade => 
    trade.target_player && (
      (trade.properties_offered && trade.properties_offered.length > 0) ||
      (trade.money_offered && trade.money_offered > 0) ||
      (trade.jail_cards_offered && trade.jail_cards_offered > 0) ||
      (trade.properties_requested && trade.properties_requested.length > 0) ||
      (trade.money_requested && trade.money_requested > 0) ||
      (trade.jail_cards_requested && trade.jail_cards_requested > 0)
    )
  );

  return (
    <div className={`
      fixed inset-0 z-50 
      flex items-center justify-center 
      transition-opacity duration-300
      ${isTransitioning ? "opacity-0" : "opacity-100"}
    `}>
      {/* Glassmorphism backdrop */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-900/70 to-purple-900/70 backdrop-blur-md" onClick={onClose}></div>
      
      {/* Modal content */}
      <div className="
        relative w-full max-w-5xl mx-4 my-6 max-h-[90vh]
        bg-gradient-to-br from-blue-600/30 to-purple-600/30 
        backdrop-blur-xl shadow-2xl
        rounded-2xl overflow-hidden
        border border-white border-opacity-20
      ">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white border-opacity-20 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Create Trade Offers</h2>
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
        <div className="px-6 py-4 border-t border-white border-opacity-20 flex justify-between">
          <div className="flex gap-3">
            <GlassButton onClick={onClose} variant="ghost">
              Close
            </GlassButton>
            <GlassButton onClick={handleCancel} variant="secondary">
              Cancel Round
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
  onReject
}) => {
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsTransitioning(true);
      setTimeout(() => {
        setIsTransitioning(false);
      }, 300);
    }
  }, [isOpen]);

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
      utility: "#444444"
    };

    if (name.includes("Gara")) return colorMap.railway;
    if (name.includes("Uzina")) return colorMap.utility;
    if (name.includes("Rahova") || name.includes("Giulesti")) return colorMap.brown;
    if (name.includes("Vitan") || name.includes("Pantelimon") || name.includes("Berceni")) return colorMap.light_blue;
    if (name.includes("Titan") || name.includes("Colentina") || name.includes("Tei")) return colorMap.pink;
    if (name.includes("Timisoara") || name.includes("Brasov") || name.includes("Taberei")) return colorMap.orange;
    if (name.includes("Carol") || name.includes("Kogalniceanu") || name.includes("Eroilor")) return colorMap.red;
    if (name.includes("Titulescu") || name.includes("Mai") || name.includes("Dorobantilor")) return colorMap.yellow;
    if (name.includes("Unirii") || name.includes("Cotroceni") || name.includes("Victoriei")) return colorMap.green;
    if (name.includes("Magheru") || name.includes("Primaverii")) return colorMap.blue;
    
    return "#cccccc";
  };

  return (
    <div className={`
      fixed inset-0 z-50 
      flex items-center justify-center 
      transition-opacity duration-300
      ${isTransitioning ? "opacity-0" : "opacity-100"}
    `}>
      {/* Glassmorphism backdrop */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-900/70 to-purple-900/70 backdrop-blur-md" onClick={onClose}></div>
      
      {/* Modal content */}
      <div className="
        relative w-full max-w-lg mx-4 
        bg-gradient-to-br from-blue-600/30 to-purple-600/30 
        backdrop-blur-xl shadow-2xl
        rounded-2xl overflow-hidden
        border border-white border-opacity-20
      ">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white border-opacity-20 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">
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
            <GlassCard className="bg-green-600/20">
              <h3 className="font-bold text-white mb-4 pb-2 border-b border-white border-opacity-20">
                You Will Receive:
              </h3>
              <div className="space-y-2">
                {/* Properties */}
                {tradeOffer.properties_offered && tradeOffer.properties_offered.length > 0 ? (
                  <div className="mb-4">
                    <h4 className="text-white text-opacity-80 text-sm mb-2">Properties:</h4>
                    <div className="space-y-1">
                      {tradeOffer.properties_offered.map((prop, idx) => (
                        <div key={idx} className="flex items-center text-white p-1 bg-white bg-opacity-10 rounded">
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
                    <h4 className="text-white text-opacity-80 text-sm mb-2">Money:</h4>
                    <div className="flex items-center text-white p-2 bg-white bg-opacity-10 rounded">
                      <DollarSign size={16} className="mr-1" />
                      <span className="font-semibold">{tradeOffer.money_offered}</span>
                    </div>
                  </div>
                )}

                {/* Jail Cards */}
                {tradeOffer.jail_cards_offered > 0 && (
                  <div>
                    <h4 className="text-white text-opacity-80 text-sm mb-2">Jail Cards:</h4>
                    <div className="flex items-center text-white p-2 bg-white bg-opacity-10 rounded">
                      <span className="font-semibold mr-1">{tradeOffer.jail_cards_offered}</span>
                      <span>Get Out of Jail Free card(s)</span>
                    </div>
                  </div>
                )}

                {/* Nothing to receive */}
                {!tradeOffer.properties_offered?.length && 
                 !tradeOffer.money_offered && 
                 !tradeOffer.jail_cards_offered && (
                  <div className="text-white text-opacity-50 italic text-center py-6">
                    Nothing to receive
                  </div>
                )}
              </div>
            </GlassCard>

            {/* What you give */}
            <GlassCard className="bg-red-600/20">
              <h3 className="font-bold text-white mb-4 pb-2 border-b border-white border-opacity-20">
                In Exchange For:
              </h3>
              <div className="space-y-2">
                {/* Properties */}
                {tradeOffer.properties_requested && tradeOffer.properties_requested.length > 0 ? (
                  <div className="mb-4">
                    <h4 className="text-white text-opacity-80 text-sm mb-2">Properties:</h4>
                    <div className="space-y-1">
                      {tradeOffer.properties_requested.map((prop, idx) => (
                        <div key={idx} className="flex items-center text-white p-1 bg-white bg-opacity-10 rounded">
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
                    <h4 className="text-white text-opacity-80 text-sm mb-2">Money:</h4>
                    <div className="flex items-center text-white p-2 bg-white bg-opacity-10 rounded">
                      <DollarSign size={16} className="mr-1" />
                      <span className="font-semibold">{tradeOffer.money_requested}</span>
                    </div>
                  </div>
                )}

                {/* Jail Cards */}
                {tradeOffer.jail_cards_requested > 0 && (
                  <div>
                    <h4 className="text-white text-opacity-80 text-sm mb-2">Jail Cards:</h4>
                    <div className="flex items-center text-white p-2 bg-white bg-opacity-10 rounded">
                      <span className="font-semibold mr-1">{tradeOffer.jail_cards_requested}</span>
                      <span>Get Out of Jail Free card(s)</span>
                    </div>
                  </div>
                )}

                {/* Nothing to give */}
                {!tradeOffer.properties_requested?.length && 
                 !tradeOffer.money_requested && 
                 !tradeOffer.jail_cards_requested && (
                  <div className="text-white text-opacity-50 italic text-center py-6">
                    Nothing to give
                  </div>
                )}
              </div>
            </GlassCard>
          </div>

          {/* Trade evaluation */}
          <div className="mt-6 p-4 bg-white bg-opacity-10 backdrop-blur-sm rounded-lg border border-white border-opacity-20">
            <h3 className="font-bold text-white mb-2">Trade Evaluation</h3>
            <p className="text-white text-opacity-80 text-sm">
              Consider if this trade benefits your overall strategy. Look at property sets, cash flow, and game position.
            </p>
          </div>
        </div>
        
        {/* Footer */}
        <div className="px-6 py-4 border-t border-white border-opacity-20 flex justify-end space-x-3">
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