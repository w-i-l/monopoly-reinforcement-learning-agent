import React from "react";
import { Dice1, Dice2, Dice3, Dice4, Dice5, Dice6 } from "lucide-react";

const DiceIcon = ({ value }) => {
  const icons = {
    1: Dice1,
    2: Dice2,
    3: Dice3,
    4: Dice4,
    5: Dice5,
    6: Dice6,
  };
  const DiceComponent = icons[value];
  return <DiceComponent className="w-12 h-12" />;
};

export default DiceIcon;
