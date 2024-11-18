const Badge = ({ children, className, onClick }) => {
  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 cursor-pointer hover:bg-blue-200 ${className}`}
    >
      {children}
    </span>
  );
};

export { Badge }; 