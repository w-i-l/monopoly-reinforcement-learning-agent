import DiceIcon from "../../Dice/Dice";
import { ModalWrapper } from "./ModalWrapper";
import { SkipAllButton } from "./SkipButton";

export const DiceRollModal = ({
  event,
  onClose,
  isVisible,
  onSkipAll,
  remainingEvents,
}) => {
  const { dice_values, total, is_doubles } = event.modal_data;

  function diceValutToDiceIcon(value) {
    switch (value) {
      case 1:
        return <DiceIcon value={1} size="large" />;
      case 2:
        return <DiceIcon value={2} size="large" />;
      case 3:
        return <DiceIcon value={3} size="large" />;
      case 4:
        return <DiceIcon value={4} size="large" />;
      case 5:
        return <DiceIcon value={5} size="large" />;
      case 6:
        return <DiceIcon value={6} size="large" />;
      default:
        return null;
    }
  }

  return (
    <ModalWrapper
      isVisible={isVisible}
      onClose={onClose}
      className="max-w-md mx-4"
    >
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
        <div className="p-6 text-center">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Dice Roll
            </h2>
            <p className="text-gray-600">{event.player}</p>
          </div>

          <div className="flex justify-center gap-4 mb-4">
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center text-2xl font-bold border border-gray-300">
              {diceValutToDiceIcon(dice_values[0])}
            </div>
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center text-2xl font-bold border border-gray-300">
              {diceValutToDiceIcon(dice_values[1])}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <p className="text-lg font-semibold text-gray-800">
              Total: {total}
            </p>
            {is_doubles && (
              <p className="text-sm text-blue-600 font-medium mt-1">
                Doubles! Roll again
              </p>
            )}
          </div>

          <div className="flex flex-row items-center gap-4">
            <button
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200"
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