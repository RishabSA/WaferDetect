import { FaChartBar, FaFileAlt, FaFlask, FaThLarge, FaWaveSquare } from "react-icons/fa";
import { NavLink, Route, Routes } from "react-router";

import DetectionViewer from "./views/DetectionViewer";
import PhysicsLab from "./views/PhysicsLab";
import Reports from "./views/Reports";
import WaferExplorer from "./views/WaferExplorer";
import YieldAnalytics from "./views/YieldAnalytics";

const views = [
  { path: "/", label: "Wafer Explorer", icon: FaThLarge },
  { path: "/yield", label: "Yield Analytics", icon: FaChartBar },
  { path: "/physics", label: "Physics Lab", icon: FaFlask },
  { path: "/reports", label: "Reports", icon: FaFileAlt },
];

const App = () => {
  return (
    <div className="flex min-h-screen bg-neutral-100 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      <aside className="flex w-60 shrink-0 flex-col gap-1 border-r border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <h1 className="mb-4 text-lg font-bold text-blue-600 dark:text-blue-400">
          WaferDetect
        </h1>
        {views.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-neutral-100 dark:hover:bg-neutral-800 ${
                isActive
                  ? "bg-blue-50 font-semibold text-blue-700 dark:bg-blue-950 dark:text-blue-300"
                  : "text-neutral-700 dark:text-neutral-300"
              }`
            }
          >
            <Icon size={14} />
            {label}
          </NavLink>
        ))}
        <div className="mt-auto flex items-center justify-between rounded-md px-3 py-2 text-sm text-neutral-400 dark:text-neutral-600">
          <span className="flex items-center gap-2">
            <FaWaveSquare size={14} />
            Line Monitor
          </span>
          <span className="rounded bg-yellow-400 px-1.5 py-0.5 text-xs font-semibold text-neutral-900 dark:bg-yellow-500 dark:text-neutral-950">
            Stage 6
          </span>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <Routes>
          <Route path="/" element={<WaferExplorer />} />
          <Route path="/wafers/:stem" element={<DetectionViewer />} />
          <Route path="/yield" element={<YieldAnalytics />} />
          <Route path="/physics" element={<PhysicsLab />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/reports/:stem" element={<Reports />} />
          <Route
            path="*"
            element={
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                Select a dashboard view.
              </p>
            }
          />
        </Routes>
      </main>
    </div>
  );
};

export default App;
