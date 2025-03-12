import React, { useState, useEffect, useRef } from "react";

const LOCAL_STORAGE_KEY = "monopoly_game_events";
const MAX_STORED_EVENTS = 100;

const EventFeed = ({ playerPort = 6060 }) => {
  const [events, setEvents] = useState(() => {
    // Initialize events from local storage if available
    try {
      const storedEvents = localStorage.getItem(LOCAL_STORAGE_KEY);
      return storedEvents ? JSON.parse(storedEvents) : [];
    } catch (error) {
      console.error("Error loading events from local storage:", error);
      return [];
    }
  });

  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const eventContainerRef = useRef(null);

  // Auto-scroll to the bottom when new events arrive
  useEffect(() => {
    if (eventContainerRef.current) {
      eventContainerRef.current.scrollTop =
        eventContainerRef.current.scrollHeight;
    }
  }, [events]);

  // Save events to local storage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(events));
    } catch (error) {
      console.error("Error saving events to local storage:", error);
    }
  }, [events]);

  // Fetch events periodically
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await fetch(
          `http://localhost:${playerPort}/api/events`
        );
        if (!response.ok) throw new Error("Failed to fetch events");

        const data = await response.json();
        if (data.events && data.events.length > 0) {
          // Add timestamp and id to events and add to state
          const newEvents = data.events.map((event) => ({
            ...event,
            id: Math.random().toString(36).substring(2, 9), // Simple unique ID
            timestamp: new Date().toLocaleTimeString(),
          }));

          setEvents((prevEvents) => {
            const updatedEvents = [...prevEvents, ...newEvents];
            // Keep only the latest MAX_STORED_EVENTS
            return updatedEvents.slice(-MAX_STORED_EVENTS);
          });
        }
      } catch (err) {
        setError(err.message);
      }
    };

    const interval = setInterval(fetchEvents, 1000);
    return () => clearInterval(interval);
  }, [playerPort]);

  // Clear events helper that also clears local storage
  const clearAllEvents = () => {
    setEvents([]);
    try {
      localStorage.removeItem(LOCAL_STORAGE_KEY);
    } catch (error) {
      console.error("Error clearing events from local storage:", error);
    }
  };

  // Filter events based on selected category
  const filteredEvents = events.filter((event) => {
    if (filter === "all") return true;
    if (filter === "money")
      return ["MONEY_RECEIVED", "MONEY_PAID", "RENT_PAID", "TAX_PAID"].includes(
        event.type
      );
    if (filter === "property")
      return [
        "PROPERTY_PURCHASED",
        "PROPERTY_MORTGAGED",
        "PROPERTY_UNMORTGAGED",
        "HOUSE_BUILT",
        "HOTEL_BUILT",
        "HOUSE_SOLD",
        "HOTEL_SOLD",
      ].includes(event.type);
    if (filter === "movement")
      return [
        "PLAYER_MOVED",
        "PLAYER_PASSED_GO",
        "PLAYER_WENT_TO_JAIL",
        "PLAYER_GOT_OUT_OF_JAIL",
      ].includes(event.type);
    return true;
  });

  // Get color for event type
  const getEventColor = (type) => {
    if (["PLAYER_MOVED", "PLAYER_GOT_OUT_OF_JAIL"].includes(type))
      return "bg-blue-50 border-blue-200";
    if (["DICE_ROLLED", "DOUBLES_ROLLED"].includes(type))
      return "bg-gray-50 border-gray-200";
    if (["PLAYER_PASSED_GO", "MONEY_RECEIVED"].includes(type))
      return "bg-green-50 border-green-200";
    if (["PROPERTY_PURCHASED", "HOUSE_BUILT", "HOTEL_BUILT"].includes(type))
      return "bg-indigo-50 border-indigo-200";
    if (
      ["MONEY_PAID", "RENT_PAID", "TAX_PAID", "PLAYER_WENT_TO_JAIL"].includes(
        type
      )
    )
      return "bg-red-50 border-red-200";
    if (["PROPERTY_MORTGAGED", "HOUSE_SOLD", "HOTEL_SOLD"].includes(type))
      return "bg-orange-50 border-orange-200";
    if (["PROPERTY_UNMORTGAGED"].includes(type))
      return "bg-emerald-50 border-emerald-200";
    if (["CHANCE_CARD_DRAWN", "COMMUNITY_CHEST_CARD_DRAWN"].includes(type))
      return "bg-yellow-50 border-yellow-200";
    if (
      ["GET_OUT_OF_JAIL_CARD_RECEIVED", "GET_OUT_OF_JAIL_CARD_USED"].includes(
        type
      )
    )
      return "bg-purple-50 border-purple-200";
    return "bg-gray-50 border-gray-200";
  };

  // Get icon for event type
  const getEventIcon = (type) => {
    const icons = {
      PLAYER_MOVED: "🚶",
      PLAYER_PASSED_GO: "💰",
      PROPERTY_PURCHASED: "🏠",
      DICE_ROLLED: "🎲",
      DOUBLES_ROLLED: "🎯",
      MONEY_RECEIVED: "💵",
      MONEY_PAID: "💸",
      RENT_PAID: "💰",
      TAX_PAID: "📝",
      PLAYER_WENT_TO_JAIL: "🔒",
      PLAYER_GOT_OUT_OF_JAIL: "🔓",
      CHANCE_CARD_DRAWN: "❓",
      COMMUNITY_CHEST_CARD_DRAWN: "📦",
      PROPERTY_MORTGAGED: "📝",
      PROPERTY_UNMORTGAGED: "📄",
      HOUSE_BUILT: "🏠",
      HOTEL_BUILT: "🏨",
      HOUSE_SOLD: "🏚️",
      HOTEL_SOLD: "🏚️",
      GET_OUT_OF_JAIL_CARD_RECEIVED: "🎫",
      GET_OUT_OF_JAIL_CARD_USED: "🎟️",
      TRADE_OFFERED: "🤝",
      TRADE_ACCEPTED: "✅",
      TRADE_REJECTED: "❌",
      TURN_STARTED: "▶️",
      TURN_ENDED: "⏹️",
    };

    return icons[type] || "📝";
  };

  return (
    <div className="bg-white shadow-lg rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 px-4 py-3">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Game Events</h2>
          <div className="flex space-x-1">
            <button
              onClick={() => setFilter("all")}
              className={`px-2 py-1 text-xs rounded-md ${
                filter === "all"
                  ? "bg-white text-blue-800"
                  : "bg-blue-700 text-blue-100"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("money")}
              className={`px-2 py-1 text-xs rounded-md ${
                filter === "money"
                  ? "bg-white text-blue-800"
                  : "bg-blue-700 text-blue-100"
              }`}
            >
              Money
            </button>
            <button
              onClick={() => setFilter("property")}
              className={`px-2 py-1 text-xs rounded-md ${
                filter === "property"
                  ? "bg-white text-blue-800"
                  : "bg-blue-700 text-blue-100"
              }`}
            >
              Property
            </button>
            <button
              onClick={() => setFilter("movement")}
              className={`px-2 py-1 text-xs rounded-md ${
                filter === "movement"
                  ? "bg-white text-blue-800"
                  : "bg-blue-700 text-blue-100"
              }`}
            >
              Movement
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          Error: {error}
        </div>
      )}

      <div
        ref={eventContainerRef}
        className="overflow-y-auto max-h-80 py-1 px-2 divide-y divide-gray-100"
      >
        {filteredEvents.length === 0 ? (
          <div className="text-gray-500 italic text-center py-6">
            No events yet. Game events will appear here.
          </div>
        ) : (
          filteredEvents.map((event) => (
            <div
              key={event.id}
              className={`p-3 my-1 rounded-md border ${getEventColor(
                event.type
              )}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{getEventIcon(event.type)}</span>
                <div className="flex-grow">
                  <p
                    className={`text-sm ${
                      event.player && event.player.includes("Strategic")
                        ? "text-red-800"
                        : "text-gray-800"
                    }`}
                  >
                    {event.description}
                    {event.amount && !event.description.includes("$") && (
                      <span className="font-semibold"> (${event.amount})</span>
                    )}
                  </p>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <div className="flex items-center">
                      <span
                        className={`w-2 h-2 rounded-full mr-1 ${
                          event.player && event.player.includes("Strategic")
                            ? "bg-red-600"
                            : "bg-blue-600"
                        }`}
                      ></span>
                      <span>{event.player}</span>
                    </div>
                    <div className="opacity-70">{event.timestamp}</div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-gray-200 p-2 flex justify-between items-center bg-gray-50">
        <span className="text-xs text-gray-500">
          {filteredEvents.length} events
        </span>
        {events.length > 0 && (
          <button
            onClick={clearAllEvents}x
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm font-medium text-gray-700"
          >
            Clear All
          </button>
        )}
      </div>
    </div>
  );
};

export default EventFeed;
