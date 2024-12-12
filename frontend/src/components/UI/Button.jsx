const Button = ({
  children,
  variant = "default",
  className = "",
  disabled = false,
  onClick,
  ...props
}) => {
  const variantStyles = {
    default: "bg-blue-500 hover:bg-blue-600 text-white",
    destructive: "bg-red-500 hover:bg-red-600 text-white",
    outline: "border border-gray-300 hover:bg-gray-100",
    ghost: "hover:bg-gray-100",
  };

  return (
    <button
      className={`
        px-4 
        py-2 
        rounded-md 
        font-medium 
        transition-colors 
        ${variantStyles[variant]}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""} 
        ${className}
      `}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
