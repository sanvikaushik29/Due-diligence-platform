
import { NavLink, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import ChatPage from "./pages/ChatPage";
import AnalysisPage from "./pages/AnalysisPage";
import DocumentsPage from "./pages/DocumentsPage";
import HistoryPage from "./pages/HistoryPage";
import "./App.css";

export default function App() {
  return (
    <div className="shell">
      <nav className="top-nav">
        <div className="brand mono">LEDGER</div>
        <div className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? "active" : ""}>Home</NavLink>
          <NavLink to="/chat" className={({ isActive }) => isActive ? "active" : ""}>Chat</NavLink>
          <NavLink to="/analysis" className={({ isActive }) => isActive ? "active" : ""}>Analysis</NavLink>
          <NavLink to="/documents" className={({ isActive }) => isActive ? "active" : ""}>Documents</NavLink>
          <NavLink to="/history" className={({ isActive }) => isActive ? "active" : ""}>History</NavLink>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/analysis" element={<AnalysisPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
