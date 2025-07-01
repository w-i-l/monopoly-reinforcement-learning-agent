import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const RentPaymentModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { property_name, rent_amount, landlord, tenant } = event.modal_data;
  const isReceiving = event.player === landlord;

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-lg mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            isReceiving
              ? "bg-green-50 border-green-100"
              : "bg-red-50 border-red-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                isReceiving ? "bg-green-100" : "bg-red-100"
              }`}
            >
              <span className="text-2xl">{isReceiving ? "💰" : "💸"}</span>
            </div>
            <div className="flex flex-col items-start">
              <h2
                className={`text-xl font-semibold ${
                  isReceiving ? "text-green-800" : "text-red-800"
                }`}
              >
                Rent {isReceiving ? "Collected" : "Paid"}
              </h2>
              <p className={isReceiving ? "text-green-600" : "text-red-600"}>
                {event.player}
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
              <span className="text-gray-600">Amount</span>
              <span
                className={`font-bold text-lg ${
                  isReceiving ? "text-green-600" : "text-red-600"
                }`}
              >
                {isReceiving ? "+" : "-"}₩{rent_amount}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Tenant</span>
              <span className="font-medium text-gray-800">{tenant}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Landlord</span>
              <span className="font-medium text-gray-800">{landlord}</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className={`w-full py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
              isReceiving
                ? "bg-green-600 hover:bg-green-700"
                : "bg-red-600 hover:bg-red-700"
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