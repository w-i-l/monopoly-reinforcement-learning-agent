import React from "react";

// Loading spinner component
const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-4">
    <div className="relative w-12 h-12">
      <div className="absolute top-0 left-0 right-0 bottom-0 rounded-full border-4 border-gray-200"></div>
      <div className="absolute top-0 left-0 right-0 bottom-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
    </div>
  </div>
);

// Button component for consistency
const Button = ({
  onClick,
  children,
  variant = "primary",
  disabled = false,
  className = "",
}) => {
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white",
    secondary: "bg-blue-100 hover:bg-blue-200 text-blue-700",
    outline: "bg-white border border-gray-300 hover:bg-gray-50 text-gray-800",
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        font-medium py-2 px-4 rounded-md transition-colors
        ${variants[variant]}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        ${className}
      `}
    >
      {children}
    </button>
  );
};

// Main pending decision card component
const PendingDecisionCard = ({
  handleDecision,
  showEventFeed,
  setShowEventFeed,
  isAIThinking = false,
  waitingForNetwork = false,
  gameState,
}) => {
  // Determine what message to show based on state
  const getMessage = () => {
    if (waitingForNetwork) {
      return "Connecting to game server...";
    }

    if (isAIThinking) {
      return "AI players are thinking...";
    }

    if (!gameState) {
      return "Loading game state...";
    }

    const currentPlayerName =
      gameState?.players?.[gameState.currentPlayer]?.name;

    if (currentPlayerName) {
      if (
        currentPlayerName.includes("Human") ||
        currentPlayerName === "Human Player"
      ) {
        return "It's your turn!";
      } else {
        return `Waiting for ${currentPlayerName} to make a move...`;
      }
    }

    return "Waiting for next decision...";
  };

  // Get game tips based on the current state
  const getGameTip = () => {
    const tips = [
      "Complete property sets to increase rent and build houses.",
      "Railroads become more valuable when you own multiple ones.",
      "The orange properties are landed on most frequently.",
      "You can mortgage properties for quick cash in emergencies.",
      "Trading is crucial for completing property sets.",
      "Don't spend all your money right away - keep some cash reserves.",
      "Build houses evenly across properties to maximize return.",
      "Landing on Free Parking does not give you money in official rules.",
      "The red, orange and yellow properties are great investments.",
      "Getting out of jail later in the game can be advantageous.",
    ];

    // Return a random tip
    return tips[Math.floor(Math.random() * tips.length)];
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 rounded-lg shadow-md mb-4 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 rounded-t-lg">
        <h3 className="font-bold text-gray-800">Game Status</h3>
      </div>

      {/* Content */}
      <div className="p-4 flex-1 overflow-y-auto">
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-2">
            {getMessage()}
          </h2>
          {(waitingForNetwork || isAIThinking || !gameState) && (
            <LoadingSpinner />
          )}
        </div>

        {/* Game stats (show only if we have game state) */}
        {gameState && (
          <div className="space-y-4 mb-6">
            {/* Player turn indicator */}
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
              <div className="text-sm text-blue-800">
                <span className="font-medium">Current Player:</span>{" "}
                {gameState?.players?.[gameState.currentPlayer]?.name}
              </div>
            </div>

            {/* Game tip */}
            <div className="bg-yellow-50 border border-yellow-100 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <span className="text-yellow-500 text-lg">💡</span>
                <div>
                  <div className="font-medium text-yellow-800 text-sm mb-1">
                    Tip
                  </div>
                  <div className="text-sm text-yellow-700">{getGameTip()}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 flex gap-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <Button
          onClick={() => handleDecision([])}
          variant="primary"
          className="flex-1"
        >
          Next Decision
        </Button>

        {/* <Button
          onClick={() => setShowEventFeed(!showEventFeed)}
          variant="secondary"
          className="flex-1"
        >
          {showEventFeed ? "Hide Events" : "Show Events"}
        </Button> */}
      </div>
    </div>
  );
};

export default PendingDecisionCard;
