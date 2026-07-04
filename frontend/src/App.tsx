import { useState } from "react";
import {
	FaBars,
	FaChartBar,
	FaCrosshairs,
	FaFlask,
	FaThLarge,
	FaTimes,
} from "react-icons/fa";
import { NavLink, Route, Routes } from "react-router";

import Detect from "./views/Detect";
import PhysicsLab from "./views/PhysicsLab";
import WaferExplorer from "./views/WaferExplorer";
import YieldAnalytics from "./views/YieldAnalytics";

const views = [
	{ path: "/", label: "Detect", icon: FaCrosshairs },
	{ path: "/explorer", label: "Wafer Explorer", icon: FaThLarge },
	{ path: "/yield", label: "Yield Analytics", icon: FaChartBar },
	{ path: "/physics", label: "Physics Lab", icon: FaFlask },
];

const navLinkClasses = (isActive: boolean): string =>
	`flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5 ${
		isActive
			? "bg-cyan-400/10 font-semibold text-cyan-300 shadow-[inset_2px_0_0_0_#22d3ee]"
			: "text-neutral-400 hover:text-neutral-200"
	}`;

const App = () => {
	const [menuOpen, setMenuOpen] = useState(false);

	const brand = (
		<div className="flex items-center gap-2.5 px-2">
			<img
				src="/assets/icon.svg"
				alt="WaferDetect"
				className="h-7 w-7 shrink-0"
			/>
			<h1 className="text-lg font-bold tracking-tight text-white">
				Wafer<span className="text-cyan-400">Detect</span>
			</h1>
		</div>
	);

	const navLinks = views.map(({ path, label, icon: Icon }) => (
		<NavLink
			key={path}
			to={path}
			onClick={() => setMenuOpen(false)}
			className={({ isActive }) => navLinkClasses(isActive)}>
			<Icon size={14} />
			{label}
		</NavLink>
	));

	return (
		<div className="flex min-h-screen flex-col text-neutral-100 md:flex-row">
			<header className="sticky top-0 z-30 flex items-center gap-2 border-b border-white/10 bg-neutral-950/80 p-3 backdrop-blur md:hidden">
				<button
					onClick={() => setMenuOpen(true)}
					aria-label="Open menu"
					className="cursor-pointer rounded-lg p-2 text-neutral-300 transition-colors hover:bg-white/5 hover:text-white">
					<FaBars size={16} />
				</button>
				{brand}
			</header>

			{menuOpen && (
				<div className="fixed inset-0 z-40 md:hidden">
					<div
						className="absolute inset-0 bg-black/60"
						onClick={() => setMenuOpen(false)}
					/>
					<nav className="absolute inset-y-0 left-0 flex w-60 flex-col gap-1 border-r border-white/10 bg-neutral-950 p-4">
						<div className="mb-4 flex items-center justify-between">
							{brand}
							<button
								onClick={() => setMenuOpen(false)}
								aria-label="Close menu"
								className="cursor-pointer rounded-lg p-2 text-neutral-400 transition-colors hover:bg-white/5 hover:text-white">
								<FaTimes size={14} />
							</button>
						</div>
						{navLinks}
					</nav>
				</div>
			)}

			<aside className="hidden w-60 shrink-0 flex-col gap-1 border-r border-white/10 bg-neutral-950/60 p-4 backdrop-blur md:flex">
				<div className="mb-6">{brand}</div>
				{navLinks}
			</aside>

			<main className="flex-1 overflow-y-auto p-4 md:p-8">
				<Routes>
					<Route path="/" element={<Detect />} />
					<Route path="/explorer" element={<WaferExplorer />} />
					<Route path="/yield" element={<YieldAnalytics />} />
					<Route path="/physics" element={<PhysicsLab />} />
					<Route
						path="*"
						element={<p className="text-sm text-neutral-400">Select a view.</p>}
					/>
				</Routes>
			</main>
		</div>
	);
};

export default App;
