import { NavLink, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ChatPage from "./pages/ChatPage";
import AnalysisPage from "./pages/AnalysisPage";
import DocumentsPage from "./pages/DocumentsPage";
import HistoryPage from "./pages/HistoryPage";
import Login from "./pages/Login";
import ProtectedRoute from "./components/ProtectedRoute";
import { logout, isAuthenticated } from "./api";
import "./App.css";

export default function App() {
  return (
    <div className="shell">
      <nav className="top-nav">
        <div className="brand mono">LEDGER</div>
        <div className="nav-links">
          <NavLink to="/" end className={({isActive}) => isActive ? "active" : ""}>Home</NavLink>
          <NavLink to="/chat" className={({isActive}) => isActive ? "active" : ""}>Chat</NavLink>
          <NavLink to="/analysis" className={({isActive}) => isActive ? "active" : ""}>Analysis</NavLink>
          <NavLink to="/documents" className={({isActive}) => isActive ? "active" : ""}>Documents</NavLink>
          <NavLink to="/history" className={({isActive}) => isActive ? "active" : ""}>History</NavLink>
          {isAuthenticated() && <button className="logout-btn" onClick={logout}>Sign out</button>}
        </div>
      </nav>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
        <Route path="/analysis" element={<ProtectedRoute><AnalysisPage /></ProtectedRoute>} />
        <Route path="/documents" element={<ProtectedRoute><DocumentsPage /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
      </Routes>
    </div>
  );
}