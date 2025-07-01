import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const CardDrawnModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { card_type, card_description } = event.modal_data;
  const isChance = card_type === "Chance";

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            isChance
              ? "bg-purple-50 border-purple-100"
              : "bg-cyan-50 border-cyan-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                isChance ? "bg-purple-100" : "bg-cyan-100"
              }`}
            >
              <span className="text-2xl">🎴</span>
            </div>
            <div>
              <h2
                className={`text-xl font-semibold ${
                  isChance ? "text-purple-800" : "text-cyan-800"
                }`}
              >
                {card_type} Card
              </h2>
              <p
                className={`${isChance ? "text-purple-600" : "text-cyan-600"}`}
              >
                {event.player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <p className="text-gray-700">{card_description}</p>
          </div>

          <button
            onClick={onClose}
            className={`w-full py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
              isChance
                ? "bg-purple-600 hover:bg-purple-700"
                : "bg-cyan-600 hover:bg-cyan-700"
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
