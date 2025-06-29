import React, { useState } from "react";
import {
  Trophy,
  TrendingUp,
  Home,
  Building,
  DollarSign,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Users,
} from "lucide-react";

const GameVictoryModal = ({ gameResult, gameState, onPlayAgain, onClose }) => {
  const [showDetailedStats, setShowDetailedStats] = useState(false);

  // Helper function to get player statistics
  const getPlayerStats = (playerName) => {
    const playerStats = gameResult.player_stats?.[playerName] || {};

    return {
      name: playerName,
      balance: playerStats.final_cash || 0,
      properties: playerStats.properties_owned || 0,
      monopolies: playerStats.monopolies_owned || 0,
      houses: playerStats.houses_built || 0,
      hotels: playerStats.hotels_built || 0,
      netWorth: playerStats.final_net_worth || 0,
      mortgaged: playerStats.properties_mortgaged || 0,
      isWinner: gameResult.winner === playerName,
      isBankrupt: gameResult.bankrupt_players?.includes(playerName) || false,
    };
  };

  // Format currency
  const formatCurrency = (amount) => {
    return `${amount.toLocaleString()}₩`;
  };

  // Get game end reason
  const getGameEndReason = () => {
    if (gameResult.bankrupt_players && gameResult.bankrupt_players.length > 0) {
      return `${gameResult.bankrupt_players.join(", ")} went bankrupt`;
    }
    if (gameResult.max_turns_reached) {
      return `Maximum turns (${gameResult.turn_count}) reached`;
    }
    if (gameResult.error) {
      return `Game ended after ${
        gameResult.turn_count || "unknown"
      } turns`;
    }
    return `Game completed after ${gameResult.turn_count || "unknown"} turns`;
  };

  // Create player stats from available data
  const createPlayerStats = () => {
    const playerNames = Object.keys(gameResult.player_stats || {});

    if (playerNames.length === 0) {
      // Fallback if no player_stats
      return [
        {
          name: "Player 1",
          balance: 0,
          properties: 0,
          monopolies: 0,
          houses: 0,
          hotels: 0,
          netWorth: 0,
          mortgaged: 0,
          isWinner: false,
          isBankrupt: false,
        },
        {
          name: "Player 2",
          balance: 0,
          properties: 0,
          monopolies: 0,
          houses: 0,
          hotels: 0,
          netWorth: 0,
          mortgaged: 0,
          isWinner: false,
          isBankrupt: false,
        },
      ];
    }

    return playerNames
      .map(getPlayerStats)
      .sort((a, b) => b.netWorth - a.netWorth);
  };

  const playerStats = createPlayerStats();
  const winner = playerStats.find((p) => p.isWinner);

  return (
    <div className="fixed inset-0 bg-gray-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl border border-gray-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-yellow-50 to-yellow-100">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
              <Trophy className="w-8 h-8 text-yellow-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Game Over!
            </h2>
            {winner && !gameResult.is_draw && (
              <div className="text-xl text-yellow-700 font-semibold">
                🎉 {winner.name} Wins! 🎉
              </div>
            )}
            {gameResult.is_draw && (
              <div className="text-xl text-blue-700 font-semibold">
                🤝 It's a Draw! 🤝
              </div>
            )}
            {!winner && !gameResult.is_draw && gameResult.error && (
              <div className="text-lg text-red-600 font-semibold">
                Game ended due to error
              </div>
            )}
            <p className="text-gray-600 text-sm mt-2">{getGameEndReason()}</p>
          </div>
        </div>

        {/* Player Leaderboard */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="w-5 h-5" />
            Final Rankings
          </h3>

          <div className="space-y-3">
            {playerStats.map((player, index) => (
              <div
                key={player.name}
                className={`p-4 rounded-lg border ${
                  player.isWinner && !gameResult.is_draw
                    ? "border-yellow-300 bg-yellow-50"
                    : player.isBankrupt
                    ? "border-red-200 bg-red-50"
                    : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                        player.isWinner && !gameResult.is_draw
                          ? "bg-yellow-500"
                          : player.isBankrupt
                          ? "bg-red-500"
                          : "bg-gray-500"
                      }`}
                    >
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900 flex items-center gap-2">
                        {player.name}
                        {player.isWinner && !gameResult.is_draw && (
                          <Trophy className="w-4 h-4 text-yellow-600" />
                        )}
                        {player.isBankrupt && (
                          <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">
                            Bankrupt
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600">
                        Net Worth: {formatCurrency(player.netWorth)}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
                      <div className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        {formatCurrency(player.balance)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Home className="w-3 h-3" />
                        {player.properties}
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {player.monopolies}
                      </div>
                      <div className="flex items-center gap-1">
                        <Building className="w-3 h-3" />
                        {player.houses + player.hotels}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detailed Statistics Toggle */}
        <div className="px-6 pb-4">
          <button
            onClick={() => setShowDetailedStats(!showDetailedStats)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors duration-200 text-gray-700"
          >
            <span className="text-sm font-medium">Detailed Statistics</span>
            {showDetailedStats ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {showDetailedStats && (
            <div className="mt-4 space-y-4">
              {playerStats.map((player) => (
                <div
                  key={player.name}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  <h4 className="font-semibold text-gray-900 mb-3">
                    {player.name}
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Cash Balance:</div>
                      <div className="font-medium">
                        {formatCurrency(player.balance)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Net Worth:</div>
                      <div className="font-medium">
                        {formatCurrency(player.netWorth)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Properties Owned:</div>
                      <div className="font-medium">{player.properties}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Monopolies:</div>
                      <div className="font-medium">{player.monopolies}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Houses Built:</div>
                      <div className="font-medium">{player.houses}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Hotels Built:</div>
                      <div className="font-medium">{player.hotels}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Mortgaged Properties:</div>
                      <div className="font-medium">{player.mortgaged}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Development Ratio:</div>
                      <div className="font-medium">
                        {player.properties > 0
                          ? (
                              (player.houses + player.hotels * 5) /
                              player.properties
                            ).toFixed(1)
                          : "0.0"}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GameVictoryModal;
