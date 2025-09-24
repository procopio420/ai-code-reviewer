import { NavLink, Route, Routes } from "react-router-dom";
import Submit from "./pages/Submit";
import History from "./pages/History";
import { ModeToggle } from "./components/theme/ModeToggle";

export default function App() {
  return (
    <div className="min-h-full">
      <header className="border-b flex justify-center">
        <div className="container py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">AI Code Reviewer</h1>
          <nav className="nav flex gap-4">
            <NavLink to="/" end>Submit</NavLink>
            <NavLink to="/history">History</NavLink>
          </nav>
          <ModeToggle />
        </div>
      </header>

      <main className="flex justify-center py-6 grid-gap ">
        <Routes>
          <Route path="/" element={<Submit />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  );
}
