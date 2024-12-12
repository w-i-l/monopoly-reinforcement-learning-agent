const Alert = ({ children, variant = "default", className = "" }) => {
  const variantStyles = {
    default: "bg-blue-100 text-blue-700 border-blue-500",
    destructive: "bg-red-100 text-red-700 border-red-500",
    warning: "bg-yellow-100 text-yellow-700 border-yellow-500",
    success: "bg-green-100 text-green-700 border-green-500",
  };

  return (
    <div
      className={`p-4 rounded-lg border ${variantStyles[variant]} ${className}`}
    >
      {children}
    </div>
  );
};

export const AlertDescription = ({ children }) => (
  <div className="text-sm">{children}</div>
);

export default Alert;
