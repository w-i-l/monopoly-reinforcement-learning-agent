import React from 'react'
import Modal from 'react-modal'
import { useState } from 'react'


const SelectPropertyModal = ({
  isOpen,
  onRequestClose,
  properties,
  onSelectProperty,
}) => {
  const [selectedProperty, setSelectedProperty] = useState("");

  const handleSelect = () => {
    onSelectProperty(selectedProperty);
    onRequestClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      contentLabel="Select Property"
      className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto mt-20"
      overlayClassName="fixed inset-0 bg-black bg-opacity-50"
    >
      <h2 className="text-xl font-bold mb-4 text-black">
        Select a Property
      </h2>
      <select
        value={selectedProperty}
        onChange={(e) => setSelectedProperty(e.target.value)}
        className="w-full p-2 border rounded mb-4 text-white"
      >
        <option value="" disabled>
          Select a property
        </option>
        {properties.map((property) => (
          <option key={property.id} value={property.name}>
            {property.name}
          </option>
        ))}
      </select>
      <div className="flex justify-end gap-2">
        <button
          onClick={onRequestClose}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 text-white"
        >
          Cancel
        </button>
        <button
          onClick={handleSelect}
          disabled={!selectedProperty}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          Select Property
        </button>
      </div>
    </Modal>
  );
};

export default SelectPropertyModal;