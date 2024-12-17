import React from 'react';
import { useState } from 'react';


const PlayerCard = ({ player, isCurrentPlayer }) => (
  <div
    className={`p-4 rounded-lg shadow-md mb-4 ${
      isCurrentPlayer ? "bg-blue-50" : "bg-white"
    }`}
  >
    <h3 className="text-lg font-bold mb-2">{player.name}</h3>
    <div className="flex flex-col gap-2">
      <p>Balance: ${player.balance}</p>
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
            {Object.entries(player.houses).map(([propertyId, count]) => {
              const property = player.properties.find(prop => prop.id === parseInt(propertyId));
              return (
                <li key={propertyId}>{`${property.name}: ${count}`}</li>
              );
            })}
          </ul>
        </div>
      )}
      {player.hotels && Object.keys(player.hotels).length > 0 && (
        <div>
          <p>Hotels:</p>
          <ul className="list-disc pl-4">
            {Object.entries(player.hotels).map(([propertyId, count]) => {
              const property = player.properties.find(prop => prop.id === parseInt(propertyId));
              return (
                <li key={propertyId}>{`${property.name}: ${count}`}</li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  </div>
);

export default PlayerCard;