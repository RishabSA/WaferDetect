export const card =
	"rounded-xl border border-neutral-900/10 bg-panel p-4 shadow-[0_1px_2px_rgba(16,24,40,0.05),0_1px_3px_rgba(16,24,40,0.08)] dark:border-white/8 dark:shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset,0_8px_24px_rgba(0,0,0,0.35)]";

// scribe-mark tick: the signature label treatment on every static panel title
export const cardTitle =
	"flex items-center gap-2 text-xs font-semibold tracking-[0.14em] text-neutral-700 uppercase before:block before:h-3 before:w-[3px] before:rounded-full before:bg-cyan-500 before:content-[''] dark:text-neutral-200 dark:before:bg-cyan-400";

export const heading =
	"text-2xl font-bold tracking-tight text-neutral-900 dark:text-white";

export const eyebrow =
	"font-mono text-[11px] font-medium tracking-[0.22em] text-cyan-700 uppercase dark:text-cyan-400/90";

export const subtle = "text-sm text-neutral-500 dark:text-neutral-400";

export const errorText = "text-sm text-red-600 dark:text-red-400";

export const select =
	"cursor-pointer rounded-lg border border-neutral-900/10 bg-inset px-2.5 py-1.5 text-sm text-neutral-700 transition-colors hover:border-cyan-600/40 focus:border-cyan-600/60 focus:ring-1 focus:ring-cyan-600/40 focus:outline-none dark:border-white/10 dark:text-neutral-200 dark:hover:border-cyan-400/40 dark:focus:border-cyan-400/60 dark:focus:ring-cyan-400/40";

export const input =
	"rounded-lg border border-neutral-900/10 bg-inset px-2.5 py-1.5 text-sm text-neutral-700 transition-colors placeholder:text-neutral-400 hover:border-cyan-600/40 focus:border-cyan-600/60 focus:ring-1 focus:ring-cyan-600/40 focus:outline-none dark:border-white/10 dark:text-neutral-200 dark:placeholder:text-neutral-600 dark:hover:border-cyan-400/40 dark:focus:border-cyan-400/60 dark:focus:ring-cyan-400/40";

export const buttonPrimary =
	"cursor-pointer rounded-lg bg-cyan-400 px-4 py-1.5 text-sm font-semibold text-cyan-950 shadow-[0_0_18px_rgba(34,211,238,0.25)] transition-all hover:bg-cyan-300 active:scale-[0.98] disabled:cursor-default disabled:bg-neutral-900/5 disabled:text-neutral-400 disabled:shadow-none dark:disabled:bg-white/5 dark:disabled:text-neutral-500";

export const buttonGhost =
	"cursor-pointer rounded-lg border border-neutral-900/10 bg-neutral-900/3 px-4 py-1.5 text-sm text-neutral-600 transition-all hover:border-cyan-600/40 hover:text-cyan-700 active:scale-[0.98] disabled:cursor-default disabled:border-neutral-900/5 disabled:bg-transparent disabled:text-neutral-400 dark:border-white/10 dark:bg-white/3 dark:text-neutral-300 dark:hover:border-cyan-400/40 dark:hover:text-cyan-300 dark:disabled:border-white/5 dark:disabled:text-neutral-600";

export const chip =
	"rounded-md border border-neutral-900/10 bg-inset px-2 py-0.5 font-mono text-[11px] text-neutral-600 dark:border-white/10 dark:text-neutral-300";

export const label =
	"font-mono text-[10px] tracking-[0.18em] text-neutral-500 uppercase";

export const segmented =
	"inline-flex items-center gap-0.5 rounded-lg border border-neutral-900/10 bg-inset p-0.5 dark:border-white/8";

export const segmentedItem = (active: boolean): string =>
	`cursor-pointer rounded-md px-3 py-1 text-sm transition-colors ${
		active
			? "bg-cyan-500/10 font-medium text-cyan-700 dark:bg-cyan-400/15 dark:text-cyan-300"
			: "text-neutral-500 hover:bg-neutral-900/5 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-white/5 dark:hover:text-neutral-200"
	}`;

export const chartTheme = (dark: boolean) => ({
	tick: {
		fill: dark ? "#8b93a3" : "#64748b",
		fontSize: 11,
		fontFamily: '"IBM Plex Mono", monospace',
	},
	axis: dark ? "#3f4654" : "#cbd5e1",
	grid: dark ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.08)",
	bar: dark ? "#22d3ee" : "#06b6d4",
	cursor: dark ? "rgba(255,255,255,0.05)" : "rgba(15,23,42,0.04)",
	tooltip: {
		backgroundColor: dark ? "#131c2b" : "#ffffff",
		border: dark
			? "1px solid rgba(255,255,255,0.12)"
			: "1px solid rgba(15,23,42,0.12)",
		borderRadius: 8,
		color: dark ? "#e5e5e5" : "#1e293b",
		fontSize: 12,
		fontFamily: '"IBM Plex Mono", monospace',
	},
});
