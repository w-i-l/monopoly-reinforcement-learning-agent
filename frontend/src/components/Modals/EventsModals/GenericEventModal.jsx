import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const GenericEventModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const getEventIcon = (type) => {
    switch (type) {
      case "TAX_PAID":
        return "🏛️";
      case "MONEY_PAID":
        return "💸";
      case "PLAYER_PASSED_GO":
        return "🔄";
      case "PLAYER_WENT_TO_JAIL":
        return "🚔";
      case "PLAYER_GOT_OUT_OF_JAIL":
        return "🗝️";
      case "HOUSE_BUILT":
        return "🏘️";
      case "HOTEL_BUILT":
        return "🏨";
      case "PROPERTY_MORTGAGED":
        return "🏦";
      case "PROPERTY_UNMORTGAGED":
        return "🏡";
      default:
        return "ℹ️";
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case "MONEY_RECEIVED":
      case "PLAYER_PASSED_GO":
      case "HOUSE_BUILT":
      case "HOTEL_BUILT":
      case "PROPERTY_UNMORTGAGED":
        return "green";
      case "TAX_PAID":
      case "MONEY_PAID":
      case "PLAYER_WENT_TO_JAIL":
      case "PROPERTY_MORTGAGED":
        return "red";
      default:
        return "blue";
    }
  };

  const color = getEventColor(event.type);

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            color === "green"
              ? "bg-green-50 border-green-100"
              : color === "red"
              ? "bg-red-50 border-red-100"
              : "bg-blue-50 border-blue-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                color === "green"
                  ? "bg-green-100"
                  : color === "red"
                  ? "bg-red-100"
                  : "bg-blue-100"
              }`}
            >
              <span className="text-2xl">{getEventIcon(event.type)}</span>
            </div>
            <div className="flex flex-col items-start">
              <h2
                className={`text-xl font-semibold ${
                  color === "green"
                    ? "text-green-800"
                    : color === "red"
                    ? "text-red-800"
                    : "text-blue-800"
                }`}
              >
                Game Event
              </h2>
              <p
                className={`${
                  color === "green"
                    ? "text-green-600"
                    : color === "red"
                    ? "text-red-600"
                    : "text-blue-600"
                }`}
              >
                {event.player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <p className="text-gray-700 mb-4">{event.description}</p>
          {event.amount && (
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <p
                className={`text-lg font-semibold ${
                  color === "green"
                    ? "text-green-600"
                    : color === "red"
                    ? "text-red-600"
                    : "text-blue-600"
                }`}
              >
                {color === "green" ? "+" : color === "red" ? "-" : ""}₩
                {event.amount}
              </p>
            </div>
          )}

          <button
            onClick={onClose}
            className={`w-full py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
              color === "green"
                ? "bg-green-600 hover:bg-green-700"
                : color === "red"
                ? "bg-red-600 hover:bg-red-700"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            Continue
          </button>

          {remainingEvents > 1 && (
            <SkipAllButton onSkipAll={onSkipAll} eventCount={remainingEvents} />
          )}
        </div>
      </div>
    </ModalWrapper>
  );
};