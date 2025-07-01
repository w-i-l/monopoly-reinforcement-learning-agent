import React from 'react'

export const SkipAllButton = ({ onSkipAll, eventCount }) => (
  <button
    onClick={onSkipAll}
    className={`bg-gray-800/90 hover:bg-gray-700/90 text-white px-6 py-2 my-2
               rounded-lg text-sm font-medium transition-colors duration-200 border border-gray-600/50`}
  >
    Skip All ({eventCount})
  </button>
);