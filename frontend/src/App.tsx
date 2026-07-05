import { useState } from "react";
import {
	FaBars,
	FaChartBar,
	FaClipboardCheck,
	FaCrosshairs,
	FaFlask,
	FaThLarge,
	FaTimes,
} from "react-icons/fa";
import { NavLink, Route, Routes } from "react-router";

import ThemeToggle from "./components/ThemeToggle";
import { label } from "./ui";
import Detect from "./views/Detect";
import Evaluation from "./views/Evaluation";
import PhysicsLab from "./views/PhysicsLab";
import WaferExplorer from "./views/WaferExplorer";
import YieldAnalytics from "./views/YieldAnalytics";

const views = [
	{ path: "/", label: "Detect", icon: FaCrosshairs },
	{ path: "/explorer", label: "Wafer Explorer", icon: FaThLarge },
	{ path: "/yield", label: "Yield Analytics", icon: FaChartBar },
	{ path: "/physics", label: "Physics Lab", icon: FaFlask },
	{ path: "/evaluation", label: "Evaluation Results", icon: FaClipboardCheck },
];

const navLinkClasses = (isActive: boolean): string =>
	`flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-neutral-900/5 dark:hover:bg-white/5 ${
		isActive
			? "bg-cyan-500/10 font-semibold text-cyan-700 dark:bg-cyan-400/10 dark:text-cyan-300"
			: "text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200"
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
			<div>
				<h1 className="text-lg leading-tight font-bold tracking-tight text-neutral-900 dark:text-white">
					Wafer<span className="text-cyan-600 dark:text-cyan-400">Detect</span>
				</h1>
				<p className="font-mono text-[9px] tracking-[0.24em] text-neutral-500 uppercase">
					Defect intelligence
				</p>
			</div>
		</div>
	);

	const sidebarFooter = (
		<div className="mt-auto flex flex-col gap-2">
			<div className="rounded-lg border border-neutral-900/10 bg-inset p-3 dark:border-white/8">
				<p className={label}>Model</p>
				<p className="mt-1 font-mono text-xs text-neutral-800 dark:text-neutral-200">
					yolo26x-seg
				</p>
				<div className="mt-2 flex items-center justify-between font-mono text-[10px]">
					<span className="text-neutral-500">mask mAP50</span>
					<span className="text-cyan-700 tabular-nums dark:text-cyan-300">
						0.852
					</span>
				</div>
				<div className="mt-1 flex items-center justify-between font-mono text-[10px]">
					<span className="text-neutral-500">inference</span>
					<span className="text-neutral-600 dark:text-neutral-300">
						single pass
					</span>
				</div>
			</div>
			<p className="px-2 font-mono text-[10px] text-neutral-400 dark:text-neutral-600">
				WaferDetect v1.0.0
			</p>
		</div>
	);

	const navLinks = views.map(({ path, label: text, icon: Icon }) => (
		<NavLink
			key={path}
			to={path}
			onClick={() => setMenuOpen(false)}
			className={({ isActive }) => navLinkClasses(isActive)}>
			<Icon size={14} />
			{text}
		</NavLink>
	));

	return (
		<div className="flex min-h-screen flex-col text-neutral-900 md:flex-row dark:text-neutral-100">
			<header className="sticky top-0 z-30 flex items-center gap-2 border-b border-neutral-900/10 bg-void/80 p-3 backdrop-blur md:hidden dark:border-white/8">
				<button
					onClick={() => setMenuOpen(true)}
					aria-label="Open menu"
					className="cursor-pointer rounded-lg p-2 text-neutral-600 transition-colors hover:bg-neutral-900/5 hover:text-neutral-900 dark:text-neutral-300 dark:hover:bg-white/5 dark:hover:text-white">
					<FaBars size={16} />
				</button>
				{brand}
			</header>

			{menuOpen && (
				<div className="fixed inset-0 z-40 md:hidden">
					<div
						className="absolute inset-0 bg-black/40 dark:bg-black/60"
						onClick={() => setMenuOpen(false)}
					/>
					<nav className="absolute inset-y-0 left-0 flex w-60 flex-col gap-1 border-r border-neutral-900/10 bg-void p-4 dark:border-white/8">
						<div className="mb-3 flex items-center justify-between">
							{brand}
							<button
								onClick={() => setMenuOpen(false)}
								aria-label="Close menu"
								className="cursor-pointer rounded-lg p-2 text-neutral-500 transition-colors hover:bg-neutral-900/5 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-white/5 dark:hover:text-white">
								<FaTimes size={14} />
							</button>
						</div>
						<div className="mb-4">
							<ThemeToggle />
						</div>
						{navLinks}
						{sidebarFooter}
					</nav>
				</div>
			)}

			<aside className="hidden w-60 shrink-0 flex-col gap-1 border-r border-neutral-900/10 p-4 md:flex dark:border-white/8">
				<div className="mb-3">{brand}</div>
				<div className="mb-6">
					<ThemeToggle />
				</div>
				<p className={`mb-1 px-3 ${label}`}>Console</p>
				{navLinks}
				{sidebarFooter}
			</aside>

			<main className="flex-1 overflow-y-auto p-4 md:p-8">
				<div className="mx-auto w-full max-w-375">
					<Routes>
						<Route path="/" element={<Detect />} />
						<Route path="/explorer" element={<WaferExplorer />} />
						<Route path="/yield" element={<YieldAnalytics />} />
						<Route path="/physics" element={<PhysicsLab />} />
						<Route path="/evaluation" element={<Evaluation />} />
						<Route
							path="*"
							element={
								<p className="text-sm text-neutral-500 dark:text-neutral-400">
									Select a view.
								</p>
							}
						/>
					</Routes>
				</div>
			</main>
		</div>
	);
};

export default App;
