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

  // Get event style based on type
  const getEventStyle = (type) => {
    const styles = {
      // Movement related
      PLAYER_MOVED: {
        bg: "bg-blue-100",
        border: "border-blue-200",
        icon: "🚶",
        iconBg: "bg-blue-200",
      },
      PLAYER_PASSED_GO: {
        bg: "bg-green-100",
        border: "border-green-200",
        icon: "💰",
        iconBg: "bg-green-200",
      },
      PLAYER_WENT_TO_JAIL: {
        bg: "bg-red-100",
        border: "border-red-200",
        icon: "🔒",
        iconBg: "bg-red-200",
      },
      PLAYER_GOT_OUT_OF_JAIL: {
        bg: "bg-blue-100",
        border: "border-blue-200",
        icon: "🔓",
        iconBg: "bg-blue-200",
      },

      // Dice related
      DICE_ROLLED: {
        bg: "bg-gray-100",
        border: "border-gray-300",
        icon: "🎲",
        iconBg: "bg-gray-200",
      },
      DOUBLES_ROLLED: {
        bg: "bg-purple-100",
        border: "border-purple-200",
        icon: "🎯",
        iconBg: "bg-purple-200",
      },

      // Money related
      MONEY_RECEIVED: {
        bg: "bg-green-100",
        border: "border-green-200",
        icon: "💵",
        iconBg: "bg-green-200",
      },
      MONEY_PAID: {
        bg: "bg-red-100",
        border: "border-red-200",
        icon: "💸",
        iconBg: "bg-red-200",
      },
      RENT_PAID: {
        bg: "bg-red-100",
        border: "border-red-200",
        icon: "💰",
        iconBg: "bg-red-200",
      },
      TAX_PAID: {
        bg: "bg-red-100",
        border: "border-red-200",
        icon: "📝",
        iconBg: "bg-red-200",
      },

      // Property related
      PROPERTY_PURCHASED: {
        bg: "bg-indigo-100",
        border: "border-indigo-200",
        icon: "🏠",
        iconBg: "bg-indigo-200",
      },
      PROPERTY_MORTGAGED: {
        bg: "bg-orange-100",
        border: "border-orange-200",
        icon: "📝",
        iconBg: "bg-orange-200",
      },
      PROPERTY_UNMORTGAGED: {
        bg: "bg-emerald-100",
        border: "border-emerald-200",
        icon: "📄",
        iconBg: "bg-emerald-200",
      },
      HOUSE_BUILT: {
        bg: "bg-indigo-100",
        border: "border-indigo-200",
        icon: "🏠",
        iconBg: "bg-indigo-200",
      },
      HOTEL_BUILT: {
        bg: "bg-indigo-100",
        border: "border-indigo-200",
        icon: "🏨",
        iconBg: "bg-indigo-200",
      },
      HOUSE_SOLD: {
        bg: "bg-orange-100",
        border: "border-orange-200",
        icon: "🏚️",
        iconBg: "bg-orange-200",
      },
      HOTEL_SOLD: {
        bg: "bg-orange-100",
        border: "border-orange-200",
        icon: "🏚️",
        iconBg: "bg-orange-200",
      },

      // Card related
      CHANCE_CARD_DRAWN: {
        bg: "bg-yellow-100",
        border: "border-yellow-200",
        icon: "❓",
        iconBg: "bg-yellow-200",
      },
      COMMUNITY_CHEST_CARD_DRAWN: {
        bg: "bg-yellow-100",
        border: "border-yellow-200",
        icon: "📦",
        iconBg: "bg-yellow-200",
      },
      GET_OUT_OF_JAIL_CARD_RECEIVED: {
        bg: "bg-purple-100",
        border: "border-purple-200",
        icon: "🎫",
        iconBg: "bg-purple-200",
      },
      GET_OUT_OF_JAIL_CARD_USED: {
        bg: "bg-purple-100",
        border: "border-purple-200",
        icon: "🎟️",
        iconBg: "bg-purple-200",
      },

      // Trade related
      TRADE_OFFERED: {
        bg: "bg-blue-100",
        border: "border-blue-200",
        icon: "🤝",
        iconBg: "bg-blue-200",
      },
      TRADE_ACCEPTED: {
        bg: "bg-green-100",
        border: "border-green-200",
        icon: "✅",
        iconBg: "bg-green-200",
      },
      TRADE_REJECTED: {
        bg: "bg-red-100",
        border: "border-red-200",
        icon: "❌",
        iconBg: "bg-red-200",
      },

      // Turn related
      TURN_STARTED: {
        bg: "bg-blue-100",
        border: "border-blue-200",
        icon: "▶️",
        iconBg: "bg-blue-200",
      },
      TURN_ENDED: {
        bg: "bg-gray-100",
        border: "border-gray-200",
        icon: "⏹️",
        iconBg: "bg-gray-200",
      },

      // Default
      DEFAULT: {
        bg: "bg-gray-100",
        border: "border-gray-200",
        icon: "📝",
        iconBg: "bg-gray-200",
      },
    };

    return styles[type] || styles.DEFAULT;
  };

  // Tab button for filters
  const FilterTab = ({ label, value }) => (
    <button
      onClick={() => setFilter(value)}
      className={`
        px-3 py-1.5 text-xs font-medium rounded-md transition-all
        ${
          filter === value
            ? "bg-white text-blue-700 shadow-sm border border-blue-200"
            : "text-gray-600 bg-gray-100 hover:bg-gray-200"
        }
      `}
    >
      {label}
    </button>
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-md overflow-hidden flex flex-col h-full">
      {/* Fixed Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-gray-800">Game Events</h2>
            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
              {filteredEvents.length} events
            </span>
          </div>
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg justify-center">
            <FilterTab label="All" value="all" />
            <FilterTab label="Money" value="money" />
            <FilterTab label="Property" value="property" />
            <FilterTab label="Movement" value="movement" />
          </div>
        </div>
      </div>

      {/* Error Message (if any) */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 mx-2 my-1 px-4 py-3 rounded-md flex-shrink-0">
          Error: {error}
        </div>
      )}

      {/* Scrollable Event List */}
      <div
        ref={eventContainerRef}
        className="overflow-y-auto flex-grow"
        style={{ scrollbarWidth: "thin" }}
      >
        {filteredEvents.length === 0 ? (
          <div className="text-gray-500 italic text-center p-8 h-full flex items-center justify-center">
            <p>No events yet. Game events will appear here.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredEvents.map((event) => {
              const style = getEventStyle(event.type);
              return (
                <div
                  key={event.id}
                  className={`p-4 ${style.bg} border-l-4 ${style.border} hover:bg-opacity-90 transition-colors`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`flex-shrink-0 w-10 h-10 rounded-full ${style.iconBg} flex items-center justify-center text-xl`}
                    >
                      {style.icon}
                    </div>
                    <div className="flex-grow">
                      <p
                        className={`text-sm font-medium ${
                          event.player && event.player.includes("Strategic")
                            ? "text-red-700"
                            : "text-gray-800"
                        }`}
                      >
                        {event.description}
                        {event.amount && !event.description.includes("$") && (
                          <span className="font-bold text-gray-900">
                            {" "}
                            (${event.amount})
                          </span>
                        )}
                      </p>
                      <div className="flex justify-between text-xs mt-1">
                        <div className="flex items-center">
                          <span
                            className={`w-2 h-2 rounded-full mr-1 ${
                              event.player && event.player.includes("Strategic")
                                ? "bg-red-500"
                                : "bg-blue-500"
                            }`}
                          ></span>
                          <span className="font-medium text-gray-600">
                            {event.player}
                          </span>
                        </div>
                        <div className="text-gray-500 font-mono">
                          {event.timestamp}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Fixed Footer */}
      <div className="border-t border-gray-200 p-3 flex justify-between items-center bg-white flex-shrink-0">
        <span className="text-xs text-gray-500">
          {events.length} total events
        </span>
        {events.length > 0 && (
          <button
            onClick={clearAllEvents}
            className="px-3 py-1.5 bg-white border border-gray-300 hover:bg-gray-100 rounded-md text-sm font-medium text-gray-700 shadow-sm transition-colors"
          >
            Clear All
          </button>
        )}
      </div>
    </div>
  );
};

export default EventFeed;
