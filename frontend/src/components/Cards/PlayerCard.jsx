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
      utility: "#000000",
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
    <div className="flex items-center justify-between p-1 bg-gray-50 rounded text-xs">
      <div className="flex items-center">
        <span className="mr-1">{style.icon}</span>
        <span
          style={{
            borderLeft: `3px solid ${style.color}`,
            paddingLeft: "4px",
          }}
        >
          {property.name}
        </span>
      </div>
    </div>
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

  return (
    <div
      className={`p-3 rounded-lg border ${
        isCurrentPlayer ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-blue-100" 
      }`}
    >
      <div className="flex justify-between items-center mb-2">
        <h3 className={`font-bold ${isCurrentPlayer ? "text-blue-700" : ""}`}>
          {name}
        </h3>
        {isCurrentPlayer && (
          <span className="text-xs px-2 py-0.5 bg-yellow-400 rounded-full">
            Current
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-1 text-center text-sm mb-2">
        <div>
          <div className="font-semibold text-blue-600">${balance}</div>
          <div className="text-xs text-gray-500">Balance</div>
        </div>
        <div>
          <div className="font-semibold text-green-600">{totalHouses}</div>
          <div className="text-xs text-gray-500">Houses</div>
        </div>
        <div>
          <div className="font-semibold text-red-600">{totalHotels}</div>
          <div className="text-xs text-gray-500">Hotels</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        <span className="text-xs bg-purple-100 px-1 py-0.5 rounded-full">
          📍 {position}
        </span>
        {in_jail && (
          <span className="text-xs bg-red-100 px-1 py-0.5 rounded-full">
            🔒 In Jail
          </span>
        )}
        {escape_jail_cards > 0 && (
          <span className="text-xs bg-blue-100 px-1 py-0.5 rounded-full">
            🎫 {escape_jail_cards}
          </span>
        )}
      </div>

      <div className="text-xs">
        <div className="font-semibold mb-1">Properties:</div>
        {properties.length === 0 ? (
          <div className="text-gray-500 italic">No properties owned</div>
        ) : (
          <div className="grid grid-cols-2 gap-1">
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
