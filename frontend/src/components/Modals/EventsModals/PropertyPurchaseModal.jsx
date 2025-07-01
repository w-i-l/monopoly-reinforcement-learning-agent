import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const PropertyPurchaseModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { property_name, property_price, player_balance_after, player_name } =
    event.modal_data;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="bg-green-50 px-6 py-4 border-b border-green-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🏠</span>
            </div>
            <div className="flex flex-col items-start">
              <h2 className="text-xl font-semibold text-green-800">
                Property Purchased
              </h2>
              <p className="text-green-600">{player_name}</p>
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
              <span className="text-gray-600">Purchase Price</span>
              <span className="font-semibold text-gray-800">
                {property_price}₩
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg font-medium transition-colors duration-200"
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
