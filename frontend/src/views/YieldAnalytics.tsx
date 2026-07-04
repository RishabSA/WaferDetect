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
import { dollars, percent } from "../format";
import {
	buttonPrimary,
	card,
	errorText,
	heading,
	input,
	select,
	subtle,
} from "../ui";

const paretoLimit = 30;

const chartTooltipStyle = {
	backgroundColor: "#111114",
	border: "1px solid rgba(255,255,255,0.15)",
	borderRadius: 8,
	color: "#e5e5e5",
};

const YieldAnalytics = () => {
	const [split, setSplit] = useState("test");
	const [stem, setStem] = useState("0101_scratch");
	const [stemInput, setStemInput] = useState("0101_scratch");

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
				["Gross dies", String(summary.gross_dies), "text-white"],
				["Failed dies", String(summary.failed_dies), "text-white"],
				["Yield", percent(summary.yield), "text-emerald-400"],
				[
					"D0 / mm²",
					summary.d0_per_mm2?.toExponential(2) ?? "n/a",
					"text-white",
				],
				["Cluster α", summary.alpha?.toFixed(2) ?? "none", "text-white"],
				["Total loss", dollars(summary.total_loss_dollars), "text-red-400"],
			]
		: [];

	return (
		<div className="flex animate-fade-up flex-col gap-5">
			<div className="flex flex-wrap items-center gap-3">
				<h2 className={heading}>Yield Analytics</h2>
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
					<span className={subtle}>first {pareto.data.wafers} wafers</span>
				)}
			</div>

			{pareto.error && <p className={errorText}>{pareto.error}</p>}
			<div className={card}>
				<h3 className="mb-2 text-sm font-semibold text-white">
					Yield loss by root cause
				</h3>
				<ResponsiveContainer width="100%" height={260}>
					<BarChart data={paretoData} layout="vertical" margin={{ left: 80 }}>
						<CartesianGrid
							strokeDasharray="3 3"
							stroke="rgba(255,255,255,0.08)"
						/>
						<XAxis
							type="number"
							stroke="#525252"
							tick={{ fill: "#a3a3a3", fontSize: 11 }}
							tickFormatter={(value: number) => dollars(value)}
						/>
						<YAxis
							type="category"
							dataKey="step"
							width={100}
							stroke="#525252"
							tick={{ fill: "#a3a3a3", fontSize: 11 }}
						/>
						<Tooltip
							formatter={value => dollars(Number(value))}
							contentStyle={chartTooltipStyle}
							cursor={{ fill: "rgba(255,255,255,0.05)" }}
						/>
						<Bar dataKey="loss" fill="#22d3ee" radius={[0, 4, 4, 0]} />
					</BarChart>
				</ResponsiveContainer>
			</div>

			<div className="flex flex-wrap items-center gap-2">
				<input
					value={stemInput}
					onChange={event => setStemInput(event.target.value)}
					onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
						if (event.key === "Enter") {
							setStem(stemInput);
						}
					}}
					className={input}
				/>
				<button onClick={() => setStem(stemInput)} className={buttonPrimary}>
					Analyze wafer
				</button>
				{panel.error && <span className={errorText}>{panel.error}</span>}
			</div>

			<div className="grid grid-cols-2 gap-3 md:grid-cols-6">
				{tiles.map(([label, value, accent]) => (
					<MetricTile key={label} label={label} value={value} accent={accent} />
				))}
			</div>

			<div className="grid gap-4 md:grid-cols-2">
				<div className={card}>
					<h3 className="mb-2 text-sm font-semibold text-white">
						Radial fail rate
					</h3>
					<ResponsiveContainer width="100%" height={220}>
						<BarChart data={radialData}>
							<CartesianGrid
								strokeDasharray="3 3"
								stroke="rgba(255,255,255,0.08)"
							/>
							<XAxis
								dataKey="bin"
								stroke="#525252"
								tick={{ fill: "#a3a3a3", fontSize: 11 }}
							/>
							<YAxis
								stroke="#525252"
								tick={{ fill: "#a3a3a3", fontSize: 11 }}
								tickFormatter={(value: number) => percent(value)}
							/>
							<Tooltip
								formatter={value => percent(Number(value))}
								contentStyle={chartTooltipStyle}
								cursor={{ fill: "rgba(255,255,255,0.05)" }}
							/>
							<Bar dataKey="rate" fill="#22d3ee" radius={[4, 4, 0, 0]} />
						</BarChart>
					</ResponsiveContainer>
				</div>
				<div className={card}>
					<h3 className="mb-2 text-sm font-semibold text-white">Zone yields</h3>
					{panel.data &&
						Object.entries(panel.data.zones).map(([zone, value]) => (
							<div key={zone} className="mb-3">
								<div className="flex justify-between text-sm text-neutral-300">
									<span>{zone}</span>
									<span className="tabular-nums">{percent(value)}</span>
								</div>
								<div className="h-1.5 rounded-full bg-white/10">
									<div
										className="h-1.5 rounded-full bg-emerald-400"
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
