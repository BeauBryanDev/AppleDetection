export function Label({ children, htmlFor }) {
  return (
    <label 
      htmlFor={htmlFor} 
      className="block text-sm font-medium text-zinc-400 mb-1 tracking-wider uppercase font-mono"
    >
      {children}
    </label>
  );
}