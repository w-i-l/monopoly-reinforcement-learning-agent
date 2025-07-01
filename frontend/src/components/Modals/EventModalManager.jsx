// Modern Sophisticated Game Modals - Clean and Clear
import React, { useState, useEffect, useRef } from "react";
import { DiceIcon } from "../Dice/Dice";
import { BankruptcyModal } from "./EventsModals/BankruptcyModal";
import { CardDrawnModal } from "./EventsModals/CardDrawnModal";
import { DiceRollModal } from "./EventsModals/DiceRollModal";
import { GenericEventModal } from "./EventsModals/GenericEventModal";
import { MoneyReceivedModal } from "./EventsModals/MoneyReceivedModal";
import { PlayerMovementModal } from "./EventsModals/PlayerMovementModal";
import { PropertyPurchaseModal } from "./EventsModals/PropertyPurchaseModal";
import { PropertyTradedModal } from "./EventsModals/PropertyTradedModal";
import { RentPaymentModal } from "./EventsModals/RentPaymentModal";
import { TradeEventModal } from "./EventsModals/TadeEventModal";

export const EventModalManager = ({ playerPort, onModalChange }) => {
  const [eventQueue, setEventQueue] = useState([]);
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [lastEventId, setLastEventId] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [viewedEvents, setViewedEvents] = useState(new Set());

  // Load viewed events from localStorage on mount
  useEffect(() => {
    const savedViewedEvents = localStorage.getItem("monopoly_viewed_events");
    if (savedViewedEvents) {
      try {
        const parsed = JSON.parse(savedViewedEvents);
        setViewedEvents(new Set(parsed));
      } catch (error) {
        console.error("Error loading viewed events:", error);
      }
    }
  }, []);

  // Save viewed events to localStorage
  const saveViewedEvents = (eventIds) => {
    const allViewed = new Set([...viewedEvents, ...eventIds]);
    setViewedEvents(allViewed);
    localStorage.setItem(
      "monopoly_viewed_events",
      JSON.stringify([...allViewed])
    );
  };

  // Cleanup function to ensure modal state is reset
  const resetModalState = () => {
    setIsModalVisible(false);
    setIsProcessing(false);
    setEventQueue([]);
    setCurrentEventIndex(0);
    if (onModalChange) onModalChange(false);
  };

  // Skip all remaining events
  const handleSkipAll = async () => {
    const remainingEvents = eventQueue.slice(currentEventIndex);
    const eventIds = remainingEvents.map((event) => event.id);

    // Mark all remaining events as viewed
    saveViewedEvents(eventIds);

    // Acknowledge all events on backend
    try {
      await fetch(`http://localhost:${playerPort}/api/events/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_ids: eventIds }),
      });
    } catch (error) {
      console.error("Error acknowledging events:", error);
    }

    // Reset modal state
    resetModalState();
  };

  // Poll for new unacknowledged events
  useEffect(() => {
    const fetchNewEvents = async () => {
      try {
        const response = await fetch(
          `http://localhost:${playerPort}/api/events/since/${lastEventId}`
        );
        if (response.ok) {
          const data = await response.json();
          if (data.events && data.events.length > 0) {
            // Filter out already viewed events
            const newUnviewedEvents = data.events.filter(
              (event) => !viewedEvents.has(event.id)
            );
            if (newUnviewedEvents.length > 0) {
              setEventQueue((prev) => [...prev, ...newUnviewedEvents]);
              setLastEventId(Math.max(...data.events.map((e) => e.id)));
            }
          }
        }
      } catch (error) {
        console.error("Error fetching new events:", error);
      }
    };

    const interval = setInterval(fetchNewEvents, 1000);
    return () => clearInterval(interval);
  }, [playerPort, lastEventId, viewedEvents]);

  // Show modal when there are events in queue
  useEffect(() => {
    if (
      eventQueue.length > 0 &&
      currentEventIndex < eventQueue.length &&
      !isModalVisible &&
      !isProcessing
    ) {
      setIsModalVisible(true);
      if (onModalChange) onModalChange(true);
    } else if (
      eventQueue.length === 0 ||
      currentEventIndex >= eventQueue.length
    ) {
      if (isModalVisible) {
        setIsModalVisible(false);
        if (onModalChange) onModalChange(false);
      }
    }
  }, [
    eventQueue,
    currentEventIndex,
    isModalVisible,
    isProcessing,
    onModalChange,
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      resetModalState();
    };
  }, []);

  const handleEventAcknowledge = async () => {
    if (isProcessing) return;

    setIsProcessing(true);
    const currentEvent = eventQueue[currentEventIndex];

    if (currentEvent) {
      // Mark event as viewed locally
      saveViewedEvents([currentEvent.id]);

      // Acknowledge the event on the backend
      try {
        await fetch(`http://localhost:${playerPort}/api/events/acknowledge`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event_ids: [currentEvent.id] }),
        });
      } catch (error) {
        console.error("Error acknowledging event:", error);
      }
    }

    // Hide current modal
    setIsModalVisible(false);

    // Check if there are more events
    const nextIndex = currentEventIndex + 1;

    if (nextIndex < eventQueue.length) {
      // More events to show - immediately show next one
      setCurrentEventIndex(nextIndex);
      setIsProcessing(false);
      setIsModalVisible(true);
    } else {
      // No more events - complete cleanup
      setTimeout(() => {
        resetModalState();
      }, 100);
    }
  };

  const renderEventModal = (event) => {
    const remainingEvents = eventQueue.length - currentEventIndex;
    const modalProps = {
      event,
      onClose: handleEventAcknowledge,
      isVisible: isModalVisible,
      onSkipAll: handleSkipAll,
      remainingEvents,
    };

    // Map events to appropriate modals
    switch (event.type) {
      case "DICE_ROLLED":
        return <DiceRollModal {...modalProps} />;
      case "PROPERTY_PURCHASED":
        return <PropertyPurchaseModal {...modalProps} />;
      case "PROPERTY_TRADED":
        return <PropertyTradedModal {...modalProps} />;
      case "MONEY_RECEIVED":
      case "PLAYER_PASSED_GO":
        return <MoneyReceivedModal {...modalProps} />;
      case "RENT_PAID":
        return <RentPaymentModal {...modalProps} />;
      case "PLAYER_MOVED":
        return <PlayerMovementModal {...modalProps} />;
      case "CHANCE_CARD_DRAWN":
      case "COMMUNITY_CHEST_CARD_DRAWN":
        return <CardDrawnModal {...modalProps} />;
      case "TRADE_OFFERED":
      case "TRADE_ACCEPTED":
      case "TRADE_EXECUTED":
        return <TradeEventModal {...modalProps} />;
      case "PLAYER_BANKRUPT":
        return <BankruptcyModal {...modalProps} />;
      default:
        return <GenericEventModal {...modalProps} />;
    }
  };

  // Safety check - if no events to show, ensure modal state is reset
  if (eventQueue.length === 0 || currentEventIndex >= eventQueue.length) {
    if (isModalVisible || isProcessing) {
      setTimeout(resetModalState, 100);
    }
    return null;
  }

  const currentEvent = eventQueue[currentEventIndex];
  if (!currentEvent) {
    resetModalState();
    return null;
  }

  return renderEventModal(currentEvent);
};

