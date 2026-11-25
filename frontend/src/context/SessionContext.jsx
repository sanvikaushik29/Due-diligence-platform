import { createContext, useContext, useState } from "react";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [results, setResults] = useState(null);
  const reset = () => setResults(null);
  return (
    <SessionContext.Provider value={{ results, setResults, reset }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}