import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const BankruptcyModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { final_balance, player_name } = event.modal_data;
  const isOpponent = event.is_opponent;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-red-50 px-6 py-4 border-b border-red-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">💀</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-red-800">Bankruptcy</h2>
              <p className="text-red-600">{player_name || event.player}</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-red-50 rounded-lg p-4 mb-4">
            <p className="text-lg font-semibold text-red-700">Game Over</p>
            <p className="text-red-600">Final Balance: ₩{final_balance}</p>
          </div>

          <p className="text-gray-600 mb-4">
            {isOpponent
              ? "A competitor has been eliminated!"
              : "You have been eliminated from the game."}
          </p>

          <button
            onClick={onClose}
            className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
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
