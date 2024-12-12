// src/services/gameAPI.js
import { API_CONFIG } from "../constants/config";

class APIError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.status = status;
    this.details = details;
    this.name = "APIError";
  }
}

const handleResponse = async (response) => {
  const contentType = response.headers.get("content-type");
  const isJson = contentType?.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new APIError(
      data.detail || "An error occurred",
      response.status,
      isJson ? data : null
    );
  }

  return data;
};

const apiRequest = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...options.headers,
      },
      ...options,
    });

    return await handleResponse(response);
  } catch (error) {
    console.error(error);
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(`Network error: ${error.message}`, 0, error);
  }
};

// Game State Management
export const fetchGameState = () => {
  return apiRequest("/api/game-state");
};

export const startNewGame = (players) => {
  return apiRequest("/api/new-game", {
    method: "POST",
    body: JSON.stringify({ players }),
  });
};

// Player Actions
export const rollDice = () => {
  return apiRequest("/api/roll-dice", {
    method: "POST",
  });
};

export const endTurn = () => {
  return apiRequest("/api/end-turn", {
    method: "POST",
  });
};

// Property Management
export const buyProperty = () => {
  return apiRequest("/api/buy-property", {
    method: "POST",
  });
};

export const mortgageProperty = (propertyName) => {
  return apiRequest("/api/mortgage-property", {
    method: "POST",
    body: JSON.stringify({ property_name: propertyName }),
  });
};

export const unmortgageProperty = (propertyName) => {
  return apiRequest("/api/unmortgage-property", {
    method: "POST",
    body: JSON.stringify({ property_name: propertyName }),
  });
};

// Building Management
export const placeHouse = (propertyName) => {
  return apiRequest("/api/place-house", {
    method: "POST",
    body: JSON.stringify({ property_name: propertyName }),
  });
};

export const placeHotel = (propertyName) => {
  return apiRequest("/api/place-hotel", {
    method: "POST",
    body: JSON.stringify({ property_name: propertyName }),
  });
};

export const sellHouse = (propertyName) => {
  return apiRequest("/api/sell-house", {
    method: "POST",
    body: JSON.stringify({ property_name: propertyName }),
  });
};

export const sellHotel = (propertyName) => {
  return apiRequest("/api/sell-hotel", {
    method: "POST",
    body: JSON.stringify({ property_name: propertyName }),
  });
};

// Financial Transactions
export const payRent = () => {
  return apiRequest("/api/pay-rent", {
    method: "POST",
  });
};

export const payTax = () => {
  return apiRequest("/api/pay-tax", {
    method: "POST",
  });
};

export const collectIncome = () => {
  return apiRequest("/api/collect-income", {
    method: "POST",
  });
};

// Special Actions
export const drawCard = (cardType) => {
  return apiRequest("/api/draw-card", {
    method: "POST",
    body: JSON.stringify({ card_type: cardType }),
  });
};

export const getOutOfJail = (method) => {
  return apiRequest("/api/get-out-of-jail", {
    method: "POST",
    body: JSON.stringify({ method }), // 'card' or 'payment'
  });
};

// Trading
export const proposeTrade = (tradeDetails) => {
  return apiRequest("/api/propose-trade", {
    method: "POST",
    body: JSON.stringify(tradeDetails),
  });
};

export const respondToTrade = (tradeId, accept) => {
  return apiRequest("/api/respond-trade", {
    method: "POST",
    body: JSON.stringify({ trade_id: tradeId, accept }),
  });
};

// Game Statistics
export const getGameStatistics = () => {
  return apiRequest("/api/statistics");
};

export const getPlayerHistory = (playerId) => {
  return apiRequest(`/api/player-history/${playerId}`);
};
