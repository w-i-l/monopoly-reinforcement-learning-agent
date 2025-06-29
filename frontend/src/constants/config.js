export const API_CONFIG = {
  BASE_URL: "http://127.0.0.1:6060",
  TIMEOUT: 5000, // 5 seconds
  RETRY_ATTEMPTS: 3,
  ENDPOINTS: {
    GAME_STATE: "/api/game-state",
    NEW_GAME: "/api/new-game",
    ROLL_DICE: "/api/roll-dice",
    END_TURN: "/api/end-turn",
    BUY_PROPERTY: "/api/buy-property",
    MORTGAGE_PROPERTY: "/api/mortgage-property",
    UNMORTGAGE_PROPERTY: "/api/unmortgage-property",
    PLACE_HOUSE: "/api/place-house",
    PLACE_HOTEL: "/api/place-hotel",
    SELL_HOUSE: "/api/sell-house",
    SELL_HOTEL: "/api/sell-hotel",
    PAY_RENT: "/api/pay-rent",
    PAY_TAX: "/api/pay-tax",
    COLLECT_INCOME: "/api/collect-income",
    DRAW_CARD: "/api/draw-card",
    GET_OUT_OF_JAIL: "/api/get-out-of-jail",
    PROPOSE_TRADE: "/api/propose-trade",
    RESPOND_TRADE: "/api/respond-trade",
    STATISTICS: "/api/statistics",
    PLAYER_HISTORY: "/api/player-history",
  },
};

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
};
