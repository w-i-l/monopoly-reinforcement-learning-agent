import React, { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  RotateCcw,
  AlertTriangle,
  Wifi,
  WifiOff,
} from "lucide-react";

const GameErrorModal = ({ error, onRetry }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const getErrorDetails = () => {
    if (typeof error === "string") {
      return error;
    }
    if (error?.message) {
      return error.message;
    }
    if (error?.status) {
      return `HTTP Error ${error.status}: ${
        error.details || "Unknown server error"
      }`;
    }
    return "Unknown connection error occurred";
  };

  const getErrorTitle = () => {
    if (typeof error === "string" && error.includes("Network error")) {
      return "Connection Lost";
    }
    if (error?.status >= 500) {
      return "Server Error";
    }
    if (error?.status >= 400) {
      return "Game Error";
    }
    return "Connection Error";
  };

  const handleRetry = async () => {
    setRetrying(true);
    try {
      await onRetry();
    } finally {
      // Reset retrying state after a short delay
      setTimeout(() => setRetrying(false), 1000);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-50 flex items-center justify-center p-4">
      {/* Main error container */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8 max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="mx-auto w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-4">
            <WifiOff className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {getErrorTitle()}
          </h2>
          <p className="text-gray-600 text-sm">
            Unable to connect to the game server. Please check your connection
            and try again.
          </p>
        </div>

        {/* Error details disclosure */}
        <div className="mb-6">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors duration-200 text-gray-700"
          >
            <span className="text-sm font-medium">Technical Details</span>
            {showDetails ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {showDetails && (
            <div className="mt-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-gray-700 text-xs font-mono break-words leading-relaxed">
                {getErrorDetails()}
              </p>
            </div>
          )}
        </div>

        {/* Retry button */}
        <button
          onClick={handleRetry}
          disabled={retrying}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 shadow-sm"
        >
          <RotateCcw className={`w-4 h-4 ${retrying ? "animate-spin" : ""}`} />
          {retrying ? "Connecting..." : "Retry Connection"}
        </button>

        {/* Status indicator */}
        <div className="mt-4 text-center">
          <div className="inline-flex items-center gap-2 text-gray-500 text-xs">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            Game server offline
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameErrorModal;