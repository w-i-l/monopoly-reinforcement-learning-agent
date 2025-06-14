import React, { useState } from "react";

// Helper components for the Decision UI
const DecisionCard = ({ title, children, actions, onSkip }) => (
  <div className="bg-white rounded-xl border border-gray-200 shadow-md overflow-hidden mb-4">
    {/* Header */}
    <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
      <h3 className="font-bold text-gray-800">{title}</h3>
      {onSkip && (
        <button
          onClick={onSkip}
          className="text-sm text-gray-500 hover:text-gray-700 flex items-center bg-gray-100 rounded-md transition-colors duration-200"
        >
          <span>Skip</span>
          <svg
            className="w-4 h-4 ml-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      )}
    </div>

    {/* Content */}
    <div className="p-4 max-h-[30vh] overflow-auto">{children}</div>

    {/* Actions */}
    {actions && (
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        {actions}
      </div>
    )}
  </div>
);

const Button = ({
  children,
  onClick,
  variant = "primary",
  disabled = false,
  className = "",
  icon,
}) => {
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white",
    secondary: "bg-gray-200 hover:bg-gray-300 text-gray-800",
    success: "bg-green-600 hover:bg-green-700 text-white",
    danger: "bg-red-600 hover:bg-red-700 text-white",
    warning: "bg-yellow-500 hover:bg-yellow-600 text-white",
    outline: "bg-white border-2 border-gray-300 hover:bg-gray-50 text-gray-800",
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex justify-center items-center gap-2
        px-4 py-2 rounded-md font-medium shadow-sm
        transition-colors duration-200
        ${variants[variant]} 
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        ${className}
      `}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

const SelectableButton = ({
  item,
  children,
  onClick,
  selected,
  className = "",
}) => (
  <button
    onClick={onClick}
    className={`
      flex items-center justify-between
      w-full px-4 py-2 my-1
      border ${
        selected
          ? "border-blue-500 bg-blue-50"
          : "border-gray-200 bg-white hover:bg-gray-50"
      }
      rounded-md shadow-sm transition-colors
      ${className}
    `}
  >
    <span className="text-gray-800 font-medium">{children}</span>
    {selected && (
      <span className="flex-shrink-0 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
        <svg
          className="w-3 h-3 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </span>
    )}
  </button>
);

const InfoItem = ({ label, value }) => (
  <div className="flex justify-between items-center px-3 py-2 rounded-md border border-gray-200 bg-gray-50 mb-2">
    <span className="text-gray-600 text-sm">{label}</span>
    <span className="text-gray-900 font-medium">{value}</span>
  </div>
);

const PropertyItem = ({ property, color, children }) => (
  <div className="border border-gray-200 rounded-md p-3 bg-white">
    <div className="flex items-center mb-2">
      <div
        className="w-4 h-4 rounded-full mr-2 flex-shrink-0"
        style={{ backgroundColor: color }}
      />
      <h4 className="font-medium text-gray-800">{property}</h4>
    </div>
    {children}
  </div>
);

// Decision Types Components
// 1. Buy Property Decision
const BuyPropertyDecision = ({ pendingDecision, handleDecision }) => {
  const { property, price, balance } = pendingDecision.data;

  return (
    <DecisionCard
      title="Buy Property?"
      onSkip={() => handleDecision(false)}
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleDecision(false)}
            className="flex-1"
          >
            Pass
          </Button>
          <Button
            variant="primary"
            onClick={() => handleDecision(true)}
            className="flex-1"
          >
            Buy Property
          </Button>
        </div>
      }
    >
      <div className="text-center mb-4">
        <div className="text-lg font-bold text-gray-800 mb-1">{property}</div>
        <div className="text-2xl font-bold text-blue-600">{price}₩</div>
      </div>

      <div className="space-y-2 my-4">
        <InfoItem label="Your Balance" value={`${balance}₩`} />
        <InfoItem
          label="Remaining Balance After Purchase"
          value={`${balance - price}₩`}
        />
      </div>

      <div className="bg-blue-50 border border-blue-200 p-3 rounded-md text-sm text-blue-800">
        <p>Would you like to purchase this property?</p>
      </div>
    </DecisionCard>
  );
};

// 2. Upgrade Properties Decision
const UpgradePropertiesDecision = ({
  pendingDecision,
  handleDecision,
  selectedItems,
  toggleSelection,
}) => {
  const colorMap = {
    brown: "#845031",
    light_blue: "#c0e0f9",
    pink: "#b63785",
    orange: "#d39423",
    red: "#c3141b",
    yellow: "#fdee01",
    green: "#5aa757",
    blue: "#1166b0",
    railway: "#000000",
    utility: "#444444",
  };

  function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
  }

  return (
    <DecisionCard
      title="Upgrade Properties"
      onSkip={() => handleDecision([])}
      actions={
        <Button
          variant="primary"
          onClick={() => handleDecision(Array.from(selectedItems))}
          disabled={selectedItems.size === 0}
          className="w-full"
        >
          Confirm Selected Upgrades ({selectedItems.size})
        </Button>
      }
    >
      <InfoItem
        label="Your Balance"
        value={`${pendingDecision.data.balance}₩`}
      />

      <h4 className="font-medium text-gray-700 mt-4 mb-2">
        Select properties to upgrade:
      </h4>
      <div className="max-h-72 overflow-y-auto pr-2">
        <div className="grid grid-cols-1 gap-4">
          {Object.entries(pendingDecision.data.grouped_properties).map(
            ([group, groupInfo]) => {
              const [props, cost] = groupInfo;
              const isSelected = selectedItems.has(group);

              return (
                <div
                  key={group}
                  className={`
                  border-2 p-3 rounded-lg transition-colors
                  ${
                    isSelected
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-blue-200"
                  }
                `}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <div
                        style={{
                          background: `${colorMap[group]}`,
                          width: "16px",
                          height: "16px",
                          borderRadius: "50%",
                          marginRight: "8px",
                        }}
                      />
                      <h4 className="font-medium text-gray-800">
                        {capitalizeFirstLetter(group)}
                      </h4>
                    </div>
                    <div className="text-sm bg-white px-2 py-1 rounded-md border border-gray-200 font-medium text-gray-700">
                      Cost: {cost}₩
                    </div>
                  </div>

                  <div className="bg-white rounded-md p-2 border border-gray-200 mb-3">
                    <div className="text-sm text-gray-600 mb-1">
                      Properties:
                    </div>
                    <div className="grid grid-cols-1 gap-1">
                      {props.map((prop, idx) => (
                        <div
                          key={idx}
                          className="text-gray-800 text-sm py-1 px-2 bg-gray-50 rounded"
                        >
                          {prop}
                        </div>
                      ))}
                    </div>
                  </div>

                  <Button
                    variant={isSelected ? "primary" : "outline"}
                    onClick={() => toggleSelection(group)}
                    className="w-full"
                  >
                    {isSelected ? "Selected" : "Select for Upgrade"}
                  </Button>
                </div>
              );
            }
          )}
        </div>
      </div>
    </DecisionCard>
  );
};

// 3. Mortgage Properties Decision
const MortgagePropertiesDecision = ({
  pendingDecision,
  handleDecision,
  selectedItems,
  toggleSelection,
}) => {
  return (
    <DecisionCard
      title="Mortgage Properties"
      onSkip={() => handleDecision([])}
      actions={
        <Button
          variant="primary"
          onClick={() => handleDecision(Array.from(selectedItems))}
          disabled={selectedItems.size === 0}
          className="w-full"
        >
          Confirm Selected Mortgages ({selectedItems.size})
        </Button>
      }
    >
      <InfoItem
        label="Your Balance"
        value={`${pendingDecision.data.balance}₩`}
      />

      <h4 className="font-medium text-gray-700 my-3">
        Select properties to mortgage:
      </h4>

      <div className="divide-y divide-gray-200 max-h-72 overflow-y-auto pr-2">
        {pendingDecision.data.properties.map((prop) => {
          const isSelected = selectedItems.has(prop);

          return (
            <SelectableButton
              key={prop}
              item={prop}
              onClick={() => toggleSelection(prop)}
              selected={isSelected}
            >
              Mortgage {prop}
            </SelectableButton>
          );
        })}
      </div>
    </DecisionCard>
  );
};

// 4. Pay Jail Fine Decision
const PayJailFineDecision = ({ pendingDecision, handleDecision }) => {
  const { balance, jail_fine } = pendingDecision.data;

  return (
    <DecisionCard
      title="Pay Jail Fine?"
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleDecision(false)}
            className="flex-1"
          >
            Stay in Jail
          </Button>
          <Button
            variant="primary"
            onClick={() => handleDecision(true)}
            className="flex-1"
          >
            Pay Fine
          </Button>
        </div>
      }
    >
      <div className="text-center mb-4">
        <div className="p-3 bg-red-100 rounded-full inline-flex">
          <span className="text-3xl">🔒</span>
        </div>
        <div className="text-lg font-medium text-gray-800 mt-2">
          You are in jail!
        </div>
      </div>

      <div className="space-y-3 my-4">
        <InfoItem label="Jail Fine" value={`${jail_fine}₩`} />
        <InfoItem label="Your Balance" value={`${balance}₩`} />
        <InfoItem
          label="Remaining Balance After Payment"
          value={`${balance - jail_fine}₩`}
        />
      </div>

      <div className="bg-blue-50 border border-blue-200 p-3 rounded-md text-sm text-blue-800">
        <p>Would you like to pay the fine to get out of jail?</p>
      </div>
    </DecisionCard>
  );
};

// 5. Use Jail Card Decision
const UseJailCardDecision = ({ pendingDecision, handleDecision }) => {
  const hasCard = pendingDecision.data.has_card;

  return (
    <DecisionCard
      title="Use Get Out of Jail Free Card?"
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleDecision(false)}
            className="flex-1"
          >
            Stay in Jail
          </Button>
          <Button
            variant="primary"
            onClick={() => handleDecision(true)}
            disabled={!hasCard}
            className="flex-1"
          >
            Use Card
          </Button>
        </div>
      }
    >
      <div className="text-center mb-4">
        <div className="p-3 bg-purple-100 rounded-full inline-flex">
          <span className="text-3xl">🎫</span>
        </div>
        <div className="text-lg font-medium text-gray-800 mt-2">
          {hasCard
            ? "You have a Get Out of Jail Free card!"
            : "You don't have a Get Out of Jail Free card"}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 p-3 rounded-md text-sm text-blue-800">
        <p>Would you like to use your card to get out of jail?</p>
      </div>
    </DecisionCard>
  );
};

// 6. Accept Trade Decision
const AcceptTradeDecision = ({
  pendingDecision,
  handleDecision,
  setShowAcceptTradeModal,
}) => {
  return (
    <DecisionCard
      title="Trade Offer"
      onSkip={() => handleDecision(false)}
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleDecision(false)}
            className="flex-1"
          >
            Reject Trade
          </Button>
          <Button
            variant="primary"
            onClick={() => setShowAcceptTradeModal(true)}
            className="flex-1"
          >
            View Trade
          </Button>
        </div>
      }
    >
      <div className="text-center mb-4">
        <div className="p-3 bg-blue-100 rounded-full inline-flex">
          <span className="text-3xl">🤝</span>
        </div>
        <div className="text-lg font-medium text-gray-800 mt-2">
          {pendingDecision.data.source_player} has offered you a trade
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 p-3 rounded-md text-sm text-blue-800">
        <p>Would you like to review this trade offer?</p>
      </div>
    </DecisionCard>
  );
};

// 7. Create Trade Decision
const CreateTradeDecision = ({
  pendingDecision,
  handleDecision,
  setShowTradeModal,
}) => {
  return (
    <DecisionCard
      title="Create Trade"
      onSkip={() => handleDecision([])}
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleDecision([])}
            className="flex-1"
          >
            Skip
          </Button>
          <Button
            variant="primary"
            onClick={() => setShowTradeModal(true)}
            className="flex-1"
          >
            Create Trade
          </Button>
        </div>
      }
    >
      <div className="text-center mb-4">
        <div className="p-3 bg-blue-100 rounded-full inline-flex">
          <span className="text-3xl">💼</span>
        </div>
        <div className="text-lg font-medium text-gray-800 mt-2">
          Would you like to create a trade offer?
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 p-3 rounded-md text-sm text-blue-800">
        <p>
          You can trade properties, money and jail cards with other players.
        </p>
      </div>
    </DecisionCard>
  );
};

// Main Decision UI component
const DecisionUI = ({
  pendingDecision,
  handleDecision,
  selectedItems,
  toggleSelection,
  setShowTradeModal,
  setShowAcceptTradeModal,
}) => {
  if (!pendingDecision) return null;

  const decisionTypes = {
    buy_property: () => (
      <BuyPropertyDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
      />
    ),

    upgrade_properties: () => (
      <UpgradePropertiesDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
        selectedItems={selectedItems}
        toggleSelection={toggleSelection}
      />
    ),

    mortgage_properties: () => (
      <MortgagePropertiesDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
        selectedItems={selectedItems}
        toggleSelection={toggleSelection}
      />
    ),

    pay_jail_fine: () => (
      <PayJailFineDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
      />
    ),

    use_jail_card: () => (
      <UseJailCardDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
      />
    ),

    accept_trade: () => (
      <AcceptTradeDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
        setShowAcceptTradeModal={setShowAcceptTradeModal}
      />
    ),

    create_trade: () => (
      <CreateTradeDecision
        pendingDecision={pendingDecision}
        handleDecision={handleDecision}
        setShowTradeModal={setShowTradeModal}
      />
    ),
  };

  return decisionTypes[pendingDecision.type]?.() || null;
};

export default DecisionUI;
