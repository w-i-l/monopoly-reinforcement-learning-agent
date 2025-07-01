// Enhanced DiceIcon.jsx - Supports different sizes and animations
import React from "react";

const DiceIcon = ({
  value,
  size = "normal",
  isRolling = false,
  className = "",
}) => {
  const getDiceDisplay = (num) => {
    const dotPositions = {
      1: [{ top: "50%", left: "50%", transform: "translate(-50%, -50%)" }],
      2: [
        { top: "25%", left: "25%" },
        { bottom: "25%", right: "25%" },
      ],
      3: [
        { top: "25%", left: "25%" },
        { top: "50%", left: "50%", transform: "translate(-50%, -50%)" },
        { bottom: "25%", right: "25%" },
      ],
      4: [
        { top: "25%", left: "25%" },
        { top: "25%", right: "25%" },
        { bottom: "25%", left: "25%" },
        { bottom: "25%", right: "25%" },
      ],
      5: [
        { top: "25%", left: "25%" },
        { top: "25%", right: "25%" },
        { top: "50%", left: "50%", transform: "translate(-50%, -50%)" },
        { bottom: "25%", left: "25%" },
        { bottom: "25%", right: "25%" },
      ],
      6: [
        { top: "25%", left: "25%" },
        { top: "25%", right: "25%" },
        { top: "50%", left: "25%", transform: "translateY(-50%)" },
        { top: "50%", right: "25%", transform: "translateY(-50%)" },
        { bottom: "25%", left: "25%" },
        { bottom: "25%", right: "25%" },
      ],
    };

    return dotPositions[num] || [];
  };

  const getSizeClasses = () => {
    switch (size) {
      case "small":
        return {
          container: "w-8 h-8 text-xs",
          dot: "w-1 h-1",
        };
      case "normal":
        return {
          container: "w-12 h-12 text-sm",
          dot: "w-1.5 h-1.5",
        };
      case "large":
        return {
          container: "w-16 h-16 text-lg",
          dot: "w-2 h-2",
        };
      case "extra-large":
        return {
          container: "w-20 h-20 text-xl",
          dot: "w-2.5 h-2.5",
        };
      default:
        return {
          container: "w-12 h-12 text-sm",
          dot: "w-1.5 h-1.5",
        };
    }
  };

  const sizeClasses = getSizeClasses();
  const dots = getDiceDisplay(value);

  return (
    <div
      className={`
        ${sizeClasses.container}
        bg-white border-2 border-gray-300 rounded-lg shadow-lg
        relative flex items-center justify-center
        transition-all duration-300 ease-out
        ${isRolling ? "animate-spin" : ""}
        ${className}
      `}
      style={{
        background: isRolling
          ? "linear-gradient(45deg, #f3f4f6, #e5e7eb)"
          : "white",
      }}
    >
      {isRolling ? (
        // Show question mark or spinning dots when rolling
        <div className="text-gray-400 font-bold animate-pulse">?</div>
      ) : (
        // Show dice dots
        dots.map((dot, index) => (
          <div
            key={index}
            className={`${sizeClasses.dot} bg-gray-800 rounded-full absolute`}
            style={dot}
          />
        ))
      )}
    </div>
  );
};

// Animated Dice Pair Component for modals
export const AnimatedDicePair = ({
  dice = [1, 1],
  isRolling = false,
  size = "large",
  onRollComplete,
}) => {
  const [currentDice, setCurrentDice] = React.useState([1, 1]);
  const [rolling, setRolling] = React.useState(false);

  React.useEffect(() => {
    if (isRolling && !rolling) {
      setRolling(true);

      // Simulate rolling animation with random values
      const rollInterval = setInterval(() => {
        setCurrentDice([
          Math.floor(Math.random() * 6) + 1,
          Math.floor(Math.random() * 6) + 1,
        ]);
      }, 100);

      // Stop rolling after animation duration
      setTimeout(() => {
        clearInterval(rollInterval);
        setCurrentDice(dice);
        setRolling(false);
        if (onRollComplete) onRollComplete();
      }, 2000);

      return () => clearInterval(rollInterval);
    }
  }, [isRolling, rolling, dice, onRollComplete]);

  const displayDice = rolling ? currentDice : dice;

  return (
    <div className="flex gap-4 justify-center items-center">
      <div
        className={`transform transition-transform duration-300 ${
          rolling ? "animate-bounce" : "hover:scale-110"
        }`}
      >
        <DiceIcon value={displayDice[0]} size={size} isRolling={rolling} />
      </div>
      <div
        className={`transform transition-transform duration-300 ${
          rolling ? "animate-bounce" : "hover:scale-110"
        }`}
        style={{ animationDelay: rolling ? "0.1s" : "0s" }}
      >
        <DiceIcon value={displayDice[1]} size={size} isRolling={rolling} />
      </div>
    </div>
  );
};

// Dice Roll Result Display Component
export const DiceRollResult = ({
  dice,
  total,
  isDoubles,
  showAnimation = false,
  className = "",
}) => {
  const [showResult, setShowResult] = React.useState(!showAnimation);

  React.useEffect(() => {
    if (showAnimation) {
      const timer = setTimeout(() => setShowResult(true), 1000);
      return () => clearTimeout(timer);
    }
  }, [showAnimation]);

  return (
    <div className={`text-center ${className}`}>
      <AnimatedDicePair
        dice={dice}
        isRolling={showAnimation && !showResult}
        size="large"
        onRollComplete={() => setShowResult(true)}
      />

      {showResult && (
        <div className="mt-4 animate-fade-in">
          <div className="text-2xl font-bold mb-2">
            Total: <span className="text-yellow-400">{total}</span>
          </div>

          {isDoubles && (
            <div className="bg-yellow-500/20 border border-yellow-400 rounded-lg p-3 mb-4">
              <div className="text-yellow-400 font-bold text-lg">
                🎉 DOUBLES! 🎉
              </div>
              <div className="text-sm text-yellow-200">
                You get another turn!
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export { DiceIcon };
export default DiceIcon;
