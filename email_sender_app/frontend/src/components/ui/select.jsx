const Select = ({ children, value, onChange, className }) => {
  return (
    <select
      value={value}
      onChange={onChange}
      className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${className}`}
    >
      {children}
    </select>
  );
};

export { Select }; 