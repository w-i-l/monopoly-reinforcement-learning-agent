// Modern Sophisticated Game Modals - Clean and Clear
import React, { useState, useEffect, useRef } from "react";
import { DiceIcon } from "../Dice/Dice";

// Clean Modal Wrapper
const ModalWrapper = ({ children, isVisible, onClose, className = "" }) => {
  const [mounted, setMounted] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    if (isVisible) {
      setMounted(true);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "hidden";
      const timer = setTimeout(() => setMounted(false), 200);
      return () => clearTimeout(timer);
    }

    return () => {
      document.body.style.overflow = "hidden";
    };
  }, [isVisible]);

  if (!mounted && !isVisible) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity duration-200 ${
        isVisible ? "opacity-100" : "opacity-0"
      } bg-black/40 backdrop-blur-sm`}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className={`relative transform transition-all duration-200 ease-out ${
          isVisible ? "scale-100 translate-y-0" : "scale-95 translate-y-2"
        } ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
};

// Skip All Events Button Component
const SkipAllButton = ({ onSkipAll, eventCount }) => (
  <button
    onClick={onSkipAll}
    className={`bg-gray-800/90 hover:bg-gray-700/90 text-white px-6 py-2 my-2
               rounded-lg text-sm font-medium transition-colors duration-200 border border-gray-600/50`}
  >
    Skip All ({eventCount})
  </button>
);

// Dice Roll Modal - Clean and Fast
export const DiceRollModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { dice_values, total, is_doubles } = event.modal_data;

  function diceValutToDiceIcon(value) {
    switch (value) {
      case 1:
        return <DiceIcon value={1} size="large" />;
      case 2:
        return <DiceIcon value={2} size="large" />;
      case 3:
        return <DiceIcon value={3} size="large" />;
      case 4:
        return <DiceIcon value={4} size="large" />;
      case 5:
        return <DiceIcon value={5} size="large" />;
      case 6:
        return <DiceIcon value={6} size="large" />;
      default:
        return null;
    }
  }

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="p-6 text-center">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Dice Roll
            </h2>
            <p className="text-gray-600">{event.player}</p>
          </div>

          <div className="flex justify-center gap-4 mb-4">
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center text-2xl font-bold border border-gray-300">
              {diceValutToDiceIcon(dice_values[0])}
            </div>
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center text-2xl font-bold border border-gray-300">
              {diceValutToDiceIcon(dice_values[1])}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <p className="text-lg font-semibold text-gray-800">
              Total: {total}
            </p>
            {is_doubles && (
              <p className="text-sm text-blue-600 font-medium mt-1">
                Doubles! Roll again
              </p>
            )}
          </div>

          <div className="flex flex-row items-center gap-4">
            <button
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              Continue
            </button>

            {remainingEvents > 1 && (
              <SkipAllButton
                onSkipAll={onSkipAll}
                eventCount={remainingEvents}
              />
            )}
          </div>
        </div>
      </div>
    </ModalWrapper>
  );
};

// Property Purchase Modal - Clear Visual Hierarchy
export const PropertyPurchaseModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { property_name, property_price, player_balance_after, player_name } =
    event.modal_data;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-green-50 px-6 py-4 border-b border-green-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🏠</span>
            </div>
            <div className="flex flex-col items-start">
              <h2 className="text-xl font-semibold text-green-800">
                Property Purchased
              </h2>
              <p className="text-green-600">{player_name}</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              {property_name}
            </h3>
          </div>

          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Purchase Price</span>
              <span className="font-semibold text-gray-800">
                {property_price}₩
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};

// Money Received Modal - Clear Financial Transaction
export const MoneyReceivedModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { amount } = event;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-green-50 px-6 py-4 border-b border-green-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">💰</span>
            </div>
            <div className="flex flex-col items-start">
              <h2 className="text-xl font-semibold text-green-800">
                Money Received
              </h2>
              <p className="text-green-600">{event.player}</p>
            </div>
          </div>
        </div>

        <div className="p-6 text-center">
          <div className="bg-green-50 rounded-lg p-4 mb-4">
            <p className="text-2xl font-bold text-green-700">₩{amount}</p>
          </div>

          <p className="text-gray-600 mb-4">{event.description}</p>

          <div className="flex flex-row items-center justify-center gap-4">
            <button
              onClick={onClose}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              Continue
            </button>

            {remainingEvents > 1 && (
              <SkipAllButton
                onSkipAll={onSkipAll}
                eventCount={remainingEvents}
              />
            )}
          </div>
        </div>
      </div>
    </ModalWrapper>
  );
};

// Rent Payment Modal - Clear Transaction Details
export const RentPaymentModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { property_name, rent_amount, landlord, tenant } = event.modal_data;
  const isReceiving = event.player === landlord;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            isReceiving
              ? "bg-green-50 border-green-100"
              : "bg-red-50 border-red-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                isReceiving ? "bg-green-100" : "bg-red-100"
              }`}
            >
              <span className="text-2xl">{isReceiving ? "💰" : "💸"}</span>
            </div>
            <div className="flex flex-col items-start">
              <h2
                className={`text-xl font-semibold ${
                  isReceiving ? "text-green-800" : "text-red-800"
                }`}
              >
                Rent {isReceiving ? "Collected" : "Paid"}
              </h2>
              <p className={isReceiving ? "text-green-600" : "text-red-600"}>
                {event.player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              {property_name}
            </h3>
          </div>

          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Amount</span>
              <span
                className={`font-bold text-lg ${
                  isReceiving ? "text-green-600" : "text-red-600"
                }`}
              >
                {isReceiving ? "+" : "-"}₩{rent_amount}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Tenant</span>
              <span className="font-medium text-gray-800">{tenant}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Landlord</span>
              <span className="font-medium text-gray-800">{landlord}</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className={`w-full py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
              isReceiving
                ? "bg-green-600 hover:bg-green-700"
                : "bg-red-600 hover:bg-red-700"
            }`}
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};

// Player Movement Modal - Immediate Clear Information
export const PlayerMovementModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { tile_name, movement_reason } = event.modal_data;

  const getMovementIcon = (reason) => {
    switch (reason) {
      case "dice_roll":
        return "🎲";
      case "card_effect":
        return "🎴";
      case "jail":
        return "🚔";
      default:
        return "📍";
    }
  };

  const getMovementType = (reason) => {
    switch (reason) {
      case "dice_roll":
        return "Dice Roll";
      case "card_effect":
        return "Card Effect";
      case "jail":
        return "Sent to Jail";
      default:
        return "Movement";
    }
  };

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-blue-50 px-6 py-4 border-b border-blue-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">
                {getMovementIcon(movement_reason)}
              </span>
            </div>
            <div className="flex flex-col items-start">
              <h2 className="text-xl font-semibold text-blue-800">
                Player Movement
              </h2>
              <p className="text-blue-600">
                {getMovementType(movement_reason)}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <p className="text-gray-600 mb-2">{event.player} moved to:</p>
            <h3 className="text-lg font-semibold text-gray-800">{tile_name}</h3>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};

// Trade Event Modal - Clear Trade Breakdown
export const TradeEventModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { trade_details } = event.modal_data;
  const isOffer = event.type === "TRADE_OFFERED";
  const isExecuted = event.type === "TRADE_EXECUTED";

  const getTradeStatus = () => {
    if (isOffer) return { title: "Trade Offered", color: "yellow" };
    if (isExecuted) return { title: "Trade Completed", color: "green" };
    return { title: "Trade Accepted", color: "blue" };
  };

  const { title, color } = getTradeStatus();

  const renderPropertyList = (properties) => {
    if (!properties || !Array.isArray(properties) || properties.length === 0) {
      return <span className="text-gray-400 italic">None</span>;
    }

    return (
      <div className="space-y-1">
        {properties.map((prop, idx) => (
          <div key={idx} className="text-sm">
            {typeof prop === "object" ? prop.name || "Unknown Property" : prop}
          </div>
        ))}
      </div>
    );
  };

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-2xl mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            color === "green"
              ? "bg-green-50 border-green-100"
              : color === "yellow"
              ? "bg-yellow-50 border-yellow-100"
              : "bg-blue-50 border-blue-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                color === "green"
                  ? "bg-green-100"
                  : color === "yellow"
                  ? "bg-yellow-100"
                  : "bg-blue-100"
              }`}
            >
              <span className="text-2xl">🤝</span>
            </div>
            <div>
              <h2
                className={`text-xl font-semibold ${
                  color === "green"
                    ? "text-green-800"
                    : color === "yellow"
                    ? "text-yellow-800"
                    : "text-blue-800"
                }`}
              >
                {title}
              </h2>
              <p
                className={`${
                  color === "green"
                    ? "text-green-600"
                    : color === "yellow"
                    ? "text-yellow-600"
                    : "text-blue-600"
                }`}
              >
                {trade_details?.source_player} ↔ {trade_details?.target_player}
              </p>
            </div>
          </div>
        </div>

        {trade_details && (
          <div className="p-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-800 mb-3 text-center">
                  {trade_details.source_player} Offers
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-1">
                      Properties
                    </p>
                    {renderPropertyList(trade_details.properties_offered)}
                  </div>
                  {trade_details.money_offered > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Money
                      </p>
                      <p className="text-green-600 font-semibold">
                        ₩{trade_details.money_offered}
                      </p>
                    </div>
                  )}
                  {trade_details.jail_cards_offered > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Jail Cards
                      </p>
                      <p>{trade_details.jail_cards_offered}</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-3 text-center">
                  {trade_details.target_player} Gives
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-1">
                      Properties
                    </p>
                    {renderPropertyList(trade_details.properties_requested)}
                  </div>
                  {trade_details.money_requested > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Money
                      </p>
                      <p className="text-green-600 font-semibold">
                        ₩{trade_details.money_requested}
                      </p>
                    </div>
                  )}
                  {trade_details.jail_cards_requested > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Jail Cards
                      </p>
                      <p>{trade_details.jail_cards_requested}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              className={`w-full mt-6 py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
                color === "green"
                  ? "bg-green-600 hover:bg-green-700"
                  : color === "yellow"
                  ? "bg-yellow-600 hover:bg-yellow-700"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              Continue
            </button>

            {remainingEvents > 1 && (
              <SkipAllButton
                onSkipAll={onSkipAll}
                eventCount={remainingEvents}
              />
            )}
          </div>
        )}
      </div>
    </ModalWrapper>
  );
};

// Generic Event Modal for other events
export const GenericEventModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const getEventIcon = (type) => {
    switch (type) {
      case "TAX_PAID":
        return "🏛️";
      case "MONEY_PAID":
        return "💸";
      case "PLAYER_PASSED_GO":
        return "🔄";
      case "PLAYER_WENT_TO_JAIL":
        return "🚔";
      case "PLAYER_GOT_OUT_OF_JAIL":
        return "🗝️";
      case "HOUSE_BUILT":
        return "🏘️";
      case "HOTEL_BUILT":
        return "🏨";
      case "PROPERTY_MORTGAGED":
        return "🏦";
      case "PROPERTY_UNMORTGAGED":
        return "🏡";
      default:
        return "ℹ️";
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case "MONEY_RECEIVED":
      case "PLAYER_PASSED_GO":
      case "HOUSE_BUILT":
      case "HOTEL_BUILT":
      case "PROPERTY_UNMORTGAGED":
        return "green";
      case "TAX_PAID":
      case "MONEY_PAID":
      case "PLAYER_WENT_TO_JAIL":
      case "PROPERTY_MORTGAGED":
        return "red";
      default:
        return "blue";
    }
  };

  const color = getEventColor(event.type);

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            color === "green"
              ? "bg-green-50 border-green-100"
              : color === "red"
              ? "bg-red-50 border-red-100"
              : "bg-blue-50 border-blue-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                color === "green"
                  ? "bg-green-100"
                  : color === "red"
                  ? "bg-red-100"
                  : "bg-blue-100"
              }`}
            >
              <span className="text-2xl">{getEventIcon(event.type)}</span>
            </div>
            <div className="flex flex-col items-start">
              <h2
                className={`text-xl font-semibold ${
                  color === "green"
                    ? "text-green-800"
                    : color === "red"
                    ? "text-red-800"
                    : "text-blue-800"
                }`}
              >
                Game Event
              </h2>
              <p
                className={`${
                  color === "green"
                    ? "text-green-600"
                    : color === "red"
                    ? "text-red-600"
                    : "text-blue-600"
                }`}
              >
                {event.player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <p className="text-gray-700 mb-4">{event.description}</p>
          {event.amount && (
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <p
                className={`text-lg font-semibold ${
                  color === "green"
                    ? "text-green-600"
                    : color === "red"
                    ? "text-red-600"
                    : "text-blue-600"
                }`}
              >
                {color === "green" ? "+" : color === "red" ? "-" : ""}₩
                {event.amount}
              </p>
            </div>
          )}

          <button
            onClick={onClose}
            className={`w-full py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
              color === "green"
                ? "bg-green-600 hover:bg-green-700"
                : color === "red"
                ? "bg-red-600 hover:bg-red-700"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};

export const EventModalManager = ({ playerPort, onModalChange }) => {
  const [eventQueue, setEventQueue] = useState([]);
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [lastEventId, setLastEventId] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [viewedEvents, setViewedEvents] = useState(new Set());

  // Load viewed events from localStorage on mount
  useEffect(() => {
    const savedViewedEvents = localStorage.getItem("monopoly_viewed_events");
    if (savedViewedEvents) {
      try {
        const parsed = JSON.parse(savedViewedEvents);
        setViewedEvents(new Set(parsed));
      } catch (error) {
        console.error("Error loading viewed events:", error);
      }
    }
  }, []);

  // Save viewed events to localStorage
  const saveViewedEvents = (eventIds) => {
    const allViewed = new Set([...viewedEvents, ...eventIds]);
    setViewedEvents(allViewed);
    localStorage.setItem(
      "monopoly_viewed_events",
      JSON.stringify([...allViewed])
    );
  };

  // Cleanup function to ensure modal state is reset
  const resetModalState = () => {
    setIsModalVisible(false);
    setIsProcessing(false);
    setEventQueue([]);
    setCurrentEventIndex(0);
    if (onModalChange) onModalChange(false);
  };

  // Skip all remaining events
  const handleSkipAll = async () => {
    const remainingEvents = eventQueue.slice(currentEventIndex);
    const eventIds = remainingEvents.map((event) => event.id);

    // Mark all remaining events as viewed
    saveViewedEvents(eventIds);

    // Acknowledge all events on backend
    try {
      await fetch(`http://localhost:${playerPort}/api/events/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_ids: eventIds }),
      });
    } catch (error) {
      console.error("Error acknowledging events:", error);
    }

    // Reset modal state
    resetModalState();
  };

  // Poll for new unacknowledged events
  useEffect(() => {
    const fetchNewEvents = async () => {
      try {
        const response = await fetch(
          `http://localhost:${playerPort}/api/events/since/${lastEventId}`
        );
        if (response.ok) {
          const data = await response.json();
          if (data.events && data.events.length > 0) {
            // Filter out already viewed events
            const newUnviewedEvents = data.events.filter(
              (event) => !viewedEvents.has(event.id)
            );
            if (newUnviewedEvents.length > 0) {
              setEventQueue((prev) => [...prev, ...newUnviewedEvents]);
              setLastEventId(Math.max(...data.events.map((e) => e.id)));
            }
          }
        }
      } catch (error) {
        console.error("Error fetching new events:", error);
      }
    };

    const interval = setInterval(fetchNewEvents, 1000);
    return () => clearInterval(interval);
  }, [playerPort, lastEventId, viewedEvents]);

  // Show modal when there are events in queue
  useEffect(() => {
    if (
      eventQueue.length > 0 &&
      currentEventIndex < eventQueue.length &&
      !isModalVisible &&
      !isProcessing
    ) {
      setIsModalVisible(true);
      if (onModalChange) onModalChange(true);
    } else if (
      eventQueue.length === 0 ||
      currentEventIndex >= eventQueue.length
    ) {
      if (isModalVisible) {
        setIsModalVisible(false);
        if (onModalChange) onModalChange(false);
      }
    }
  }, [
    eventQueue,
    currentEventIndex,
    isModalVisible,
    isProcessing,
    onModalChange,
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      resetModalState();
    };
  }, []);

  const handleEventAcknowledge = async () => {
    if (isProcessing) return;

    setIsProcessing(true);
    const currentEvent = eventQueue[currentEventIndex];

    if (currentEvent) {
      // Mark event as viewed locally
      saveViewedEvents([currentEvent.id]);

      // Acknowledge the event on the backend
      try {
        await fetch(`http://localhost:${playerPort}/api/events/acknowledge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event_ids: [currentEvent.id] }),
        });
      } catch (error) {
        console.error("Error acknowledging event:", error);
      }
    }

    // Hide current modal
    setIsModalVisible(false);

    // Check if there are more events
    const nextIndex = currentEventIndex + 1;

    if (nextIndex < eventQueue.length) {
      // More events to show - immediately show next one
      setCurrentEventIndex(nextIndex);
      setIsProcessing(false);
      setIsModalVisible(true);
    } else {
      // No more events - complete cleanup
      setTimeout(() => {
        resetModalState();
      }, 100);
    }
  };

  const renderEventModal = (event) => {
    const remainingEvents = eventQueue.length - currentEventIndex;
    const modalProps = {
      event,
      onClose: handleEventAcknowledge,
      isVisible: isModalVisible,
      onSkipAll: handleSkipAll,
      remainingEvents,
    };

    // Map events to appropriate modals
    switch (event.type) {
      case "DICE_ROLLED":
        return <DiceRollModal {...modalProps} />;
      case "PROPERTY_PURCHASED":
        return <PropertyPurchaseModal {...modalProps} />;
      case "PROPERTY_TRADED":
        return <PropertyTradedModal {...modalProps} />;
      case "MONEY_RECEIVED":
      case "PLAYER_PASSED_GO":
        return <MoneyReceivedModal {...modalProps} />;
      case "RENT_PAID":
        return <RentPaymentModal {...modalProps} />;
      case "PLAYER_MOVED":
        return <PlayerMovementModal {...modalProps} />;
      case "CHANCE_CARD_DRAWN":
      case "COMMUNITY_CHEST_CARD_DRAWN":
        return <CardDrawnModal {...modalProps} />;
      case "TRADE_OFFERED":
      case "TRADE_ACCEPTED":
      case "TRADE_EXECUTED":
        return <TradeEventModal {...modalProps} />;
      case "PLAYER_BANKRUPT":
        return <BankruptcyModal {...modalProps} />;
      default:
        return <GenericEventModal {...modalProps} />;
    }
  };

  // Safety check - if no events to show, ensure modal state is reset
  if (eventQueue.length === 0 || currentEventIndex >= eventQueue.length) {
    if (isModalVisible || isProcessing) {
      setTimeout(resetModalState, 100);
    }
    return null;
  }

  const currentEvent = eventQueue[currentEventIndex];
  if (!currentEvent) {
    resetModalState();
    return null;
  }

  return renderEventModal(currentEvent);
};

// PropertyTradedModal for the modern system
export const PropertyTradedModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { property_name, from_player, to_player, trade_details } =
    event.modal_data;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-purple-50 px-6 py-4 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🤝</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-purple-800">
                Property Traded
              </h2>
              <p className="text-purple-600">
                {from_player} → {to_player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              {property_name}
            </h3>
          </div>

          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">From</span>
              <span className="font-medium text-red-600">{from_player}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">To</span>
              <span className="font-medium text-green-600">{to_player}</span>
            </div>
            {trade_details && trade_details.money_involved > 0 && (
              <div className="flex justify-between items-center py-2">
                <span className="text-gray-600">Money Involved</span>
                <span className="font-semibold text-blue-600">
                  ₩{trade_details.money_involved}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};

// CardDrawnModal for the modern system
export const CardDrawnModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { card_type, card_description } = event.modal_data;
  const isChance = card_type === "Chance";

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            isChance
              ? "bg-purple-50 border-purple-100"
              : "bg-cyan-50 border-cyan-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                isChance ? "bg-purple-100" : "bg-cyan-100"
              }`}
            >
              <span className="text-2xl">🎴</span>
            </div>
            <div>
              <h2
                className={`text-xl font-semibold ${
                  isChance ? "text-purple-800" : "text-cyan-800"
                }`}
              >
                {card_type} Card
              </h2>
              <p
                className={`${isChance ? "text-purple-600" : "text-cyan-600"}`}
              >
                {event.player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <p className="text-gray-700">{card_description}</p>
          </div>

          <button
            onClick={onClose}
            className={`w-full py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
              isChance
                ? "bg-purple-600 hover:bg-purple-700"
                : "bg-cyan-600 hover:bg-cyan-700"
            }`}
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};

// BankruptcyModal for the modern system
export const BankruptcyModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { final_balance, player_name } = event.modal_data;
  const isOpponent = event.is_opponent;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-red-50 px-6 py-4 border-b border-red-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">💀</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-red-800">Bankruptcy</h2>
              <p className="text-red-600">{player_name || event.player}</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-red-50 rounded-lg p-4 mb-4">
            <p className="text-lg font-semibold text-red-700">Game Over</p>
            <p className="text-red-600">Final Balance: ₩{final_balance}</p>
          </div>

          <p className="text-gray-600 mb-4">
            {isOpponent
              ? "A competitor has been eliminated!"
              : "You have been eliminated from the game."}
          </p>

          <button
            onClick={onClose}
            className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};
