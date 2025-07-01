import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const TradeEventModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { trade_details } = event.modal_data;
  const isOffer = event.type === "TRADE_OFFERED";
  const isExecuted = event.type === "TRADE_EXECUTED";

  const getTradeStatus = () => {
    if (isOffer) return { title: "Trade Offered", color: "yellow" };
    if (isExecuted) return { title: "Trade Completed", color: "green" };
    return { title: "Trade Accepted", color: "blue" };
  };

  const { title, color } = getTradeStatus();

  const renderPropertyList = (properties) => {
    if (!properties || !Array.isArray(properties) || properties.length === 0) {
      return <span className="text-gray-400 italic">None</span>;
    }

    return (
      <div className="space-y-1">
        {properties.map((prop, idx) => (
          <div key={idx} className="text-sm">
            {typeof prop === "object" ? prop.name || "Unknown Property" : prop}
          </div>
        ))}
      </div>
    );
  };

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-2xl mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div
          className={`px-6 py-4 border-b ${
            color === "green"
              ? "bg-green-50 border-green-100"
              : color === "yellow"
              ? "bg-yellow-50 border-yellow-100"
              : "bg-blue-50 border-blue-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                color === "green"
                  ? "bg-green-100"
                  : color === "yellow"
                  ? "bg-yellow-100"
                  : "bg-blue-100"
              }`}
            >
              <span className="text-2xl">🤝</span>
            </div>
            <div>
              <h2
                className={`text-xl font-semibold ${
                  color === "green"
                    ? "text-green-800"
                    : color === "yellow"
                    ? "text-yellow-800"
                    : "text-blue-800"
                }`}
              >
                {title}
              </h2>
              <p
                className={`${
                  color === "green"
                    ? "text-green-600"
                    : color === "yellow"
                    ? "text-yellow-600"
                    : "text-blue-600"
                }`}
              >
                {trade_details?.source_player} ↔ {trade_details?.target_player}
              </p>
            </div>
          </div>
        </div>

        {trade_details && (
          <div className="p-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-gray-800 mb-3 text-center">
                  {trade_details.source_player} Offers
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-1">
                      Properties
                    </p>
                    {renderPropertyList(trade_details.properties_offered)}
                  </div>
                  {trade_details.money_offered > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Money
                      </p>
                      <p className="text-green-600 font-semibold">
                        ₩{trade_details.money_offered}
                      </p>
                    </div>
                  )}
                  {trade_details.jail_cards_offered > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Jail Cards
                      </p>
                      <p>{trade_details.jail_cards_offered}</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-800 mb-3 text-center">
                  {trade_details.target_player} Gives
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-1">
                      Properties
                    </p>
                    {renderPropertyList(trade_details.properties_requested)}
                  </div>
                  {trade_details.money_requested > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Money
                      </p>
                      <p className="text-green-600 font-semibold">
                        ₩{trade_details.money_requested}
                      </p>
                    </div>
                  )}
                  {trade_details.jail_cards_requested > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        Jail Cards
                      </p>
                      <p>{trade_details.jail_cards_requested}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              className={`w-full mt-6 py-2 rounded-lg font-medium transition-colors duration-200 text-white ${
                color === "green"
                  ? "bg-green-600 hover:bg-green-700"
                  : color === "yellow"
                  ? "bg-yellow-600 hover:bg-yellow-700"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
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
        )}
      </div>
    </ModalWrapper>
  );
};