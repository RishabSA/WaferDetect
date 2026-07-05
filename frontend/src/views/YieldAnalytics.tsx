import type { KeyboardEvent } from "react";
import { useState } from "react";
import {
	Bar,
	BarChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

import { api, useApi } from "../api";
import MetricTile from "../components/MetricTile";
import PageHeader from "../components/PageHeader";
import { dollars, percent } from "../format";
import { useIsDark } from "../theme";
import {
	buttonPrimary,
	card,
	cardTitle,
	chartTheme,
	errorText,
	input,
	select,
	subtle,
} from "../ui";

const paretoLimit = 30;

const YieldAnalytics = () => {
	const [split, setSplit] = useState("test");
	const [stem, setStem] = useState("0487_combo_random+edge_loc+comet");
	const [stemInput, setStemInput] = useState(
		"0487_combo_random+edge_loc+comet",
	);
	const isDark = useIsDark();
	const chart = chartTheme(isDark);

	const pareto = useApi(() => api.pareto(split, paretoLimit), [split]);
	const panel = useApi(() => api.yieldWafer(stem), [stem]);

	const paretoData = (pareto.data?.pareto ?? []).map(([step, loss]) => ({
		step,
		loss,
	}));
	const radialData = (panel.data?.radial ?? []).map((rate, index) => ({
		bin: `r${index}`,
		rate,
	}));
	const summary = panel.data?.summary;
	const tiles = summary
		? [
				[
					"Gross dies",
					String(summary.gross_dies),
					"text-neutral-900 dark:text-neutral-100",
				],
				[
					"Failed dies",
					String(summary.failed_dies),
					"text-neutral-900 dark:text-neutral-100",
				],
				[
					"Yield",
					percent(summary.yield),
					"text-emerald-600 dark:text-emerald-400",
				],
				[
					"D0 / mm²",
					summary.d0_per_mm2?.toExponential(2) ?? "n/a",
					"text-neutral-900 dark:text-neutral-100",
				],
				[
					"Cluster α",
					summary.alpha?.toFixed(2) ?? "none",
					"text-neutral-900 dark:text-neutral-100",
				],
				[
					"Total loss",
					dollars(summary.total_loss_dollars),
					"text-red-600 dark:text-red-400",
				],
			]
		: [];

	return (
		<div className="flex animate-fade-up flex-col gap-5">
			<PageHeader kicker="Fab economics" title="Yield Analytics">
				<select
					value={split}
					onChange={event => setSplit(event.target.value)}
					className={select}>
					{["train", "val", "test"].map(value => (
						<option key={value} value={value}>
							{value}
						</option>
					))}
				</select>
				{pareto.data && (
					<span className={`font-mono text-xs tabular-nums ${subtle}`}>
						first {pareto.data.wafers} wafers
					</span>
				)}
			</PageHeader>

			{pareto.error && <p className={errorText}>{pareto.error}</p>}
			<div className={card}>
				<h3 className={`mb-2 ${cardTitle}`}>Yield loss by root cause</h3>
				<ResponsiveContainer width="100%" height={260}>
					<BarChart data={paretoData} layout="vertical" margin={{ left: 80 }}>
						<CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
						<XAxis
							type="number"
							stroke={chart.axis}
							tick={chart.tick}
							tickFormatter={(value: number) => dollars(value)}
						/>
						<YAxis
							type="category"
							dataKey="step"
							width={100}
							stroke={chart.axis}
							tick={chart.tick}
						/>
						<Tooltip
							formatter={value => dollars(Number(value))}
							contentStyle={chart.tooltip}
							cursor={{ fill: chart.cursor }}
						/>
						<Bar dataKey="loss" fill={chart.bar} radius={[0, 4, 4, 0]} />
					</BarChart>
				</ResponsiveContainer>
			</div>

			<div className={card}>
				<h3 className={cardTitle}>Wafer lookup</h3>
				<div className="mt-3 flex flex-wrap items-center gap-2">
					<input
						value={stemInput}
						onChange={event => setStemInput(event.target.value)}
						onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
							if (event.key === "Enter") {
								setStem(stemInput);
							}
						}}
						className={`w-full max-w-sm font-mono text-xs ${input}`}
					/>
					<button onClick={() => setStem(stemInput)} className={buttonPrimary}>
						Analyze wafer
					</button>
					{panel.error && <span className={errorText}>{panel.error}</span>}
				</div>

				<div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-6">
					{tiles.map(([label, value, accent]) => (
						<MetricTile key={label} label={label} value={value} accent={accent} />
					))}
				</div>
			</div>

			<div className="grid gap-4 md:grid-cols-2">
				<div className={card}>
					<h3 className={`mb-2 ${cardTitle}`}>Radial fail rate</h3>
					<ResponsiveContainer width="100%" height={220}>
						<BarChart data={radialData}>
							<CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
							<XAxis dataKey="bin" stroke={chart.axis} tick={chart.tick} />
							<YAxis
								stroke={chart.axis}
								tick={chart.tick}
								tickFormatter={(value: number) => percent(value)}
							/>
							<Tooltip
								formatter={value => percent(Number(value))}
								contentStyle={chart.tooltip}
								cursor={{ fill: chart.cursor }}
							/>
							<Bar dataKey="rate" fill={chart.bar} radius={[4, 4, 0, 0]} />
						</BarChart>
					</ResponsiveContainer>
				</div>
				<div className={card}>
					<h3 className={`mb-3 ${cardTitle}`}>Zone yields</h3>
					{panel.data &&
						Object.entries(panel.data.zones).map(([zone, value]) => (
							<div key={zone} className="mb-3">
								<div className="flex justify-between text-sm text-neutral-600 dark:text-neutral-300">
									<span>{zone}</span>
									<span className="font-mono text-xs tabular-nums">
										{percent(value)}
									</span>
								</div>
								<div className="mt-1 h-1.5 rounded-full bg-neutral-900/10 dark:bg-white/10">
									<div
										className="h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400"
										style={{ width: `${value * 100}%` }}
									/>
								</div>
							</div>
						))}
				</div>
			</div>
		</div>
	);
};

export default YieldAnalytics;
