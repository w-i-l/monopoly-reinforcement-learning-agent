import React, { useState, useEffect, useRef } from "react";


export const ModalWrapper = ({ children, isVisible, onClose, className = "" }) => {
  const [mounted, setMounted] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    if (isVisible) {
      setMounted(true);
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "hidden";
      const timer = setTimeout(() => setMounted(false), 200);
      return () => clearTimeout(timer);
    }

    return () => {
      document.body.style.overflow = "hidden";
    };
  }, [isVisible]);

  if (!mounted && !isVisible) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity duration-200 ${
        isVisible ? "opacity-100" : "opacity-0"
      } bg-black/40 backdrop-blur-sm`}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className={`relative transform transition-all duration-200 ease-out ${
          isVisible ? "scale-100 translate-y-0" : "scale-95 translate-y-2"
        } ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
};
