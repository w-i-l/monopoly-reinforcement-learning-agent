// src/components/Board/BoardSquare.jsx
import React from "react";
import PropTypes, { number } from "prop-types";

const BoardSquare = ({
  property,
  index,
  players,
  ownedProperties,
  mortgagedProperties,
  houses,
  hotels,
}) => {
  const playersHere = players?.filter((p) => p.position === index) || [];
  const playersColors = ["red", "blue", "green", "purple"];
  const isOwned = ownedProperties?.includes(property.id);
  const isMortgaged = mortgagedProperties?.includes(property.id);

  const getBackgroundColor = () => {
    if (
      property.type === "special" ||
      property.type === "chest" ||
      property.type === "chance" ||
      property.type === "tax"
    ) {
      return "#dfdfdf";
    }

    // const colorMap = {
    //   brown: "bg-yellow-900",
    //   lightblue: "bg-blue-300",
    //   pink: "bg-pink-400",
    //   orange: "bg-orange-500",
    //   red: "bg-red-600",
    //   yellow: "bg-yellow-400",
    //   green: "bg-green-600",
    //   darkblue: "bg-blue-800",
    //   railroad: "bg-gray-200",
    //   utility: "bg-gray-300",
    // };

    return property.color || "white";
  };

  const getTextColor = () => {
    const darkColors = ["brown", "darkblue", "green", "red"];
    return darkColors.includes(property.color) ? "text-white" : "text-black";
  };

  return (
    <div
      className={`
        w-20 h-20 
        border border-gray-300 
        flex flex-col 
        items-center 
        justify-center 
        relative 
        p-1
        ${getTextColor()}
        ${isMortgaged ? "opacity-50" : ""}
      `}
      style={{
        backgroundColor: getBackgroundColor(),
        width: "100%",
      }}
    >
      <span className="text-xxs text-center font-medium">{property.name}</span>

      {property.price && (
        <span className="text-xxs mt-1">${property.price}</span>
      )}

      {isOwned && (
        <div
          className="absolute top-1 right-1 w-3 h-3 bg-yellow-400 rounded-full"
          title="Owned"
        />
      )}

      {playersHere.map((player, i) => (
        <div
          key={i}
          className="absolute w-4 h-4 rounded-full flex items-center justify-center"
          style={{
            backgroundColor: playersColors[Number(player.name.slice(-1)) % 4],
            top: `${i * 20 + 5}%`,
            right: "5%",
          }}
        >
          <span className="text-white text-xxs font-bold">
            {player.name.slice(-1)}
          </span>
        </div>
      ))}

      {(hotels > 0 || houses > 0) && (
        <div className="absolute bottom-0 left-1 flex flex-row items-center gap-1">
          {hotels > 0 && (
            <span className="h-4 text-[10px] leading-4 font-bold bg-red-500 text-white px-1 rounded flex items-center">
              🏨 {hotels}
            </span>
          )}
          {houses > 0 && (
            <span className="h-4 text-[10px] leading-4 font-bold bg-green-500 text-white px-1 rounded flex items-center">
              🏠 {houses}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

BoardSquare.propTypes = {
  property: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    color: PropTypes.string,
    price: PropTypes.number,
    type: PropTypes.string,
  }).isRequired,
  index: PropTypes.number.isRequired,
  players: PropTypes.array,
  ownedProperties: PropTypes.array,
  mortgagedProperties: PropTypes.array,
  houses: PropTypes.number,
  hotels: PropTypes.number,
};

BoardSquare.defaultProps = {
  players: [],
  ownedProperties: [],
  mortgagedProperties: [],
  houses: 0,
  hotels: 0,
};

export default BoardSquare;
