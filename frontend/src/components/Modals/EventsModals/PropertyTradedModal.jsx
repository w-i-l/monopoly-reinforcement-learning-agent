import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const PropertyTradedModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { property_name, from_player, to_player, trade_details } =
    event.modal_data;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-purple-50 px-6 py-4 border-b border-purple-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🤝</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-purple-800">
                Property Traded
              </h2>
              <p className="text-purple-600">
                {from_player} → {to_player}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              {property_name}
            </h3>
          </div>

          <div className="space-y-3 mb-6">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">From</span>
              <span className="font-medium text-red-600">{from_player}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">To</span>
              <span className="font-medium text-green-600">{to_player}</span>
            </div>
            {trade_details && trade_details.money_involved > 0 && (
              <div className="flex justify-between items-center py-2">
                <span className="text-gray-600">Money Involved</span>
                <span className="font-semibold text-blue-600">
                  ₩{trade_details.money_involved}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
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