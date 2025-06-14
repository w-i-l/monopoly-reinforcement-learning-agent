import React from "react";

// Helper function to determine property group from name
const findPropertyGroup = (propertyName) => {
  const groupMap = {
    // Brown
    Rahova: "brown",
    Giulesti: "brown",
    // Light Blue
    Vitan: "light_blue",
    Pantelimon: "light_blue",
    Berceni: "light_blue",
    // Pink
    Titan: "pink",
    Colentina: "pink",
    Tei: "pink",
    // Orange
    "B-dul Timisoara": "orange",
    "B-dul Brasov": "orange",
    "Drumul Taberei": "orange",
    // Red
    "B-dul Carol": "red",
    "B-dul Kogalniceanu": "red",
    "B-dul Eroilor": "red",
    // Yellow
    "B-dul Titulescu": "yellow",
    "B-dul 1 Mai": "yellow",
    "Calea Dorobantilor": "yellow",
    // Green
    "Piata Unirii": "green",
    Cotroceni: "green",
    "Calea Victoriei": "green",
    // Blue
    "B-dul Magheru": "blue",
    "B-dul Primaverii": "blue",
    // Railways
    "Gara Progresul": "railway",
    "Gara Obor": "railway",
    "Gara Basarab": "railway",
    "Gara de Nord": "railway",
    // Utilities
    "Uzina Electrica": "utility",
    "Uzina de Apa": "utility",
  };

  return groupMap[propertyName] || "unknown";
};

// Property item component for displaying properties with proper styling
const PropertyItem = ({ property }) => {
  // Helper to determine property type and styling
  const getPropertyStyle = () => {
    // Color map for property groups
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
      unknown: "#cccccc",
    };

    const propType = findPropertyGroup(property.name);

    if (propType === "railway") {
      return { icon: "🚂", color: colorMap.railway };
    } else if (propType === "utility") {
      return { icon: "💡", color: colorMap.utility };
    } else {
      return { icon: "🏠", color: colorMap[propType] || colorMap.unknown };
    }
  };

  const style = getPropertyStyle();

  return (
    <div className="flex items-center p-1.5 bg-white rounded-md border border-gray-200 shadow-sm transition-all hover:bg-gray-50">
      <div
        className="w-3 h-3 rounded-full mr-1.5 flex-shrink-0"
        style={{ backgroundColor: style.color }}
      ></div>
      <span className="text-gray-700 truncate text-xs">{property.name}</span>
    </div>
  );
};

// Badge component for player stats and status
const Badge = ({ children, color = "gray" }) => {
  const colorClasses = {
    gray: "bg-gray-100 text-gray-700 border-gray-200",
    blue: "bg-blue-100 text-blue-700 border-blue-200",
    red: "bg-red-100 text-red-700 border-red-200",
    green: "bg-green-100 text-green-700 border-green-200",
    purple: "bg-purple-100 text-purple-700 border-purple-200",
    yellow: "bg-yellow-100 text-yellow-700 border-yellow-200",
  };

  return (
    <span
      className={`px-2 py-0.5 rounded-md text-xs font-medium border ${colorClasses[color]}`}
    >
      {children}
    </span>
  );
};

const PlayerCard = ({ player, isCurrentPlayer }) => {
  const {
    name,
    balance,
    properties,
    houses,
    hotels,
    escape_jail_cards,
    in_jail,
    position,
  } = player;

  // Calculate total houses and hotels
  const totalHouses = Object.values(houses || {}).reduce(
    (sum, count) => sum + count,
    0
  );
  const totalHotels = Object.values(hotels || {}).reduce(
    (sum, count) => sum + count,
    0
  );

  // Extract first letter of name for avatar
  const initial = name.charAt(0).toUpperCase();

  return (
    <div
      className={`
        rounded-xl p-4 transition-all
        ${
          isCurrentPlayer
            ? "bg-white border-2 border-blue-300 shadow-md"
            : "bg-gray-50 border border-gray-200 shadow-sm hover:bg-white"
        }
      `}
    >
      {/* Player header */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 ${
              isCurrentPlayer
                ? "bg-blue-500 text-white"
                : "bg-gray-300 text-gray-700"
            }`}
          >
            {initial}
          </div>
          <h3
            className={`font-bold ${
              isCurrentPlayer ? "text-blue-700" : "text-gray-800"
            }`}
          >
            {name}
          </h3>
        </div>
        {isCurrentPlayer && (
          <div className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium border border-yellow-200">
            Current
          </div>
        )}
      </div>

      {/* Player stats */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-white rounded-lg p-2 text-center border border-gray-200 shadow-sm">
          <div className="font-bold text-blue-600">{balance}₩</div>
          <div className="text-xs text-gray-500">Balance</div>
        </div>
        <div className="bg-white rounded-lg p-2 text-center border border-gray-200 shadow-sm">
          <div className="font-bold text-green-600">{totalHouses}</div>
          <div className="text-xs text-gray-500">Houses</div>
        </div>
        <div className="bg-white rounded-lg p-2 text-center border border-gray-200 shadow-sm">
          <div className="font-bold text-red-600">{totalHotels}</div>
          <div className="text-xs text-gray-500">Hotels</div>
        </div>
      </div>

      {/* Player status badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        <Badge color="blue">📍 Position {position}</Badge>
        {in_jail && <Badge color="red">🔒 In Jail</Badge>}
        {escape_jail_cards > 0 && (
          <Badge color="purple">
            🎫 {escape_jail_cards} Card{escape_jail_cards > 1 ? "s" : ""}
          </Badge>
        )}
      </div>

      {/* Properties section */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-gray-700">Properties</h4>
          <span className="text-xs text-gray-500">
            {properties.length} owned
          </span>
        </div>

        {properties.length === 0 ? (
          <div className="text-gray-500 italic text-xs bg-white rounded-md p-2 text-center border border-gray-200">
            No properties owned
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-1.5 max-h-36 overflow-y-auto pr-1 pb-1">
            {properties.map((prop, i) => (
              <PropertyItem key={i} property={prop} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlayerCard;
