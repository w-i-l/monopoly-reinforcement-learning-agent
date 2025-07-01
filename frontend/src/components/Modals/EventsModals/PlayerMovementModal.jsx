import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const PlayerMovementModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { tile_name, movement_reason } = event.modal_data;

  const getMovementIcon = (reason) => {
    switch (reason) {
      case "dice_roll":
        return "🎲";
      case "card_effect":
        return "🎴";
      case "jail":
        return "🚔";
      default:
        return "📍";
    }
  };

  const getMovementType = (reason) => {
    switch (reason) {
      case "dice_roll":
        return "Dice Roll";
      case "card_effect":
        return "Card Effect";
      case "jail":
        return "Sent to Jail";
      default:
        return "Movement";
    }
  };

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-blue-50 px-6 py-4 border-b border-blue-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">
                {getMovementIcon(movement_reason)}
              </span>
            </div>
            <div className="flex flex-col items-start">
              <h2 className="text-xl font-semibold text-blue-800">
                Player Movement
              </h2>
              <p className="text-blue-600">
                {getMovementType(movement_reason)}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <p className="text-gray-600 mb-2">{event.player} moved to:</p>
            <h3 className="text-lg font-semibold text-gray-800">{tile_name}</h3>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
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
