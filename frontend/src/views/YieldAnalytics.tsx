import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api, useApi } from "../api";
import { dollars, percent } from "../format";

const paretoLimit = 30;

const YieldAnalytics = () => {
  const [split, setSplit] = useState("test");
  const [stem, setStem] = useState("0101_scratch");
  const [stemInput, setStemInput] = useState("0101_scratch");

  const pareto = useApi(() => api.pareto(split, paretoLimit), [split]);
  const panel = useApi(() => api.yieldWafer(stem), [stem]);

  const paretoData = (pareto.data?.pareto ?? []).map(([step, loss]) => ({ step, loss }));
  const radialData = (panel.data?.radial ?? []).map((rate, index) => ({ bin: `r${index}`, rate }));
  const summary = panel.data?.summary;
  const tiles = summary
    ? [
        ["Gross dies", String(summary.gross_dies)],
        ["Failed dies", String(summary.failed_dies)],
        ["Yield", percent(summary.yield)],
        ["D0 / mm2", summary.d0_per_mm2?.toExponential(2) ?? "n/a"],
        ["Cluster alpha", summary.alpha?.toFixed(2) ?? "none"],
        ["Total loss", dollars(summary.total_loss_dollars)],
      ]
    : [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          Yield Analytics
        </h2>
        <select
          value={split}
          onChange={(event) => setSplit(event.target.value)}
          className="rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm text-neutral-900 transition-colors dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
        >
          {["train", "val", "test"].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        {pareto.data && (
          <span className="text-sm text-neutral-500 dark:text-neutral-400">
            first {pareto.data.wafers} wafers
          </span>
        )}
      </div>

      {pareto.error && <p className="text-sm text-red-500 dark:text-red-400">{pareto.error}</p>}
      <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <h3 className="mb-2 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
          Yield loss by root cause
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={paretoData} layout="vertical" margin={{ left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tickFormatter={(value: number) => dollars(value)} />
            <YAxis type="category" dataKey="step" width={100} />
            <Tooltip formatter={(value) => dollars(Number(value))} />
            <Bar dataKey="loss" fill="#2563eb" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          value={stemInput}
          onChange={(event) => setStemInput(event.target.value)}
          className="rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm text-neutral-900 transition-colors dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
        />
        <button
          onClick={() => setStem(stemInput)}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400"
        >
          Analyze wafer
        </button>
        {panel.error && <span className="text-sm text-red-500 dark:text-red-400">{panel.error}</span>}
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        {tiles.map(([label, value]) => (
          <div
            key={label}
            className="rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900"
          >
            <p className="text-xs text-neutral-500 dark:text-neutral-400">{label}</p>
            <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
          <h3 className="mb-2 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            Radial fail rate
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={radialData}>
              <XAxis dataKey="bin" />
              <YAxis tickFormatter={(value: number) => percent(value)} />
              <Tooltip formatter={(value) => percent(Number(value))} />
              <Bar dataKey="rate" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
          <h3 className="mb-2 text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            Zone yields
          </h3>
          {panel.data &&
            Object.entries(panel.data.zones).map(([zone, value]) => (
              <div key={zone} className="mb-2">
                <div className="flex justify-between text-sm text-neutral-700 dark:text-neutral-300">
                  <span>{zone}</span>
                  <span>{percent(value)}</span>
                </div>
                <div className="h-2 rounded bg-neutral-200 dark:bg-neutral-800">
                  <div className="h-2 rounded bg-green-500 dark:bg-green-400" style={{ width: `${value * 100}%` }} />
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default YieldAnalytics;
