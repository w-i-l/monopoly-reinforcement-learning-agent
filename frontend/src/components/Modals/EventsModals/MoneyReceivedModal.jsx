import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const MoneyReceivedModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { amount } = event;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-green-50 px-6 py-4 border-b border-green-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">💰</span>
            </div>
            <div className="flex flex-col items-start">
              <h2 className="text-xl font-semibold text-green-800">
                Money Received
              </h2>
              <p className="text-green-600">{event.player}</p>
            </div>
          </div>
        </div>

        <div className="p-6 text-center">
          <div className="bg-green-50 rounded-lg p-4 mb-4">
            <p className="text-2xl font-bold text-green-700">₩{amount}</p>
          </div>

          <p className="text-gray-600 mb-4">{event.description}</p>

          <div className="flex flex-row items-center justify-center gap-4">
            <button
              onClick={onClose}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              Continue
            </button>

            {remainingEvents > 1 && (
              <SkipAllButton
                onSkipAll={onSkipAll}
                eventCount={remainingEvents}
              />
            )}
          </div>
        </div>
      </div>
    </ModalWrapper>
  );
};
