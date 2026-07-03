import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { FaUpload } from "react-icons/fa";
import { Link, useSearchParams } from "react-router";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { AnalyzeResponse } from "../api";
import { api, useApi, waferCategories, waferImageUrl } from "../api";
import DiagnosisCard from "../components/DiagnosisCard";
import MetricTile from "../components/MetricTile";
import { overlayColors, WaferCanvas } from "../components/WaferCanvas";
import { dollars, percent, png } from "../format";
import { buttonPrimary, card, chip, errorText, heading, select, subtle } from "../ui";
import useCountUp from "../useCountUp";

const demoStem = "0101_scratch";
const galleryLimit = 14;

const viewTabs = [
  { key: "detections", label: "Detections" },
  { key: "dots", label: "Defect dots" },
] as const;
type ViewKey = (typeof viewTabs)[number]["key"];

const chartTooltipStyle = {
  backgroundColor: "#111114",
  border: "1px solid rgba(255,255,255,0.15)",
  borderRadius: 8,
  color: "#e5e5e5",
};

const summaryTitle =
  "cursor-pointer text-sm font-semibold text-white select-none marker:text-cyan-400";

const Analyze = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const stem = searchParams.get("stem") ?? demoStem;
  const [file, setFile] = useState<File | null>(null);
  const [view, setView] = useState<ViewKey>("detections");
  const [hidden, setHidden] = useState<number[]>([]);
  const [category, setCategory] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const analysis = useApi<AnalyzeResponse>(
    () => (file ? api.analyzeFile(file) : api.analyze(stem)),
    [stem, file],
  );
  const gallery = useApi(() => api.wafers({ category, limit: galleryLimit }), [category]);

  useEffect(() => setHidden([]), [analysis.data]);

  const data = analysis.data;
  const summary = data?.wafer_summary;
  const lossValue = useCountUp(summary?.total_loss_dollars ?? 0);
  const yieldValue = useCountUp((summary?.yield ?? 0) * 100);

  const selectWafer = (nextStem: string) => {
    setFile(null);
    setSearchParams({ stem: nextStem });
  };

  const onUpload = (nextFile: File | undefined) => {
    if (nextFile) {
      setFile(nextFile);
    }
  };

  const toggleHidden = (index: number) =>
    setHidden(
      hidden.includes(index) ? hidden.filter((item) => item !== index) : [...hidden, index],
    );

  const topDefect = data?.detections.length
    ? [...data.detections].sort((a, b) => b.yield_loss.dollars - a.yield_loss.dollars)[0]
    : null;

  const overlays = (data?.detections ?? []).map((detection, index) => ({
    points: detection.polygon,
    label: detection.class,
    color: overlayColors[index % overlayColors.length],
    visible: !hidden.includes(index),
  }));

  const radialData = (data?.radial ?? []).map((rate, index) => ({ bin: `r${index}`, rate }));

  return (
    <div className="flex animate-fade-up flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className={heading}>Wafer Intelligence</h2>
        <span className={chip}>{file ? file.name : stem}</span>
        {analysis.loading && (
          <span className="text-sm text-cyan-300 animate-pulse">analyzing…</span>
        )}
        <div className="ml-auto">
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event: ChangeEvent<HTMLInputElement>) => onUpload(event.target.files?.[0])}
          />
          <button onClick={() => fileRef.current?.click()} className={buttonPrimary}>
            <span className="flex items-center gap-2">
              <FaUpload size={12} />
              Upload wafer
            </span>
          </button>
        </div>
      </div>

      {analysis.error && (
        <p className={errorText}>
          {analysis.error}
          {analysis.error.includes("503") &&
            " — start the API with --model-path to enable analysis."}
        </p>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,3fr)_minmax(0,5fr)]">
        <div className="flex flex-col gap-3">
          <div className="flex gap-1.5">
            {viewTabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setView(tab.key)}
                className={`cursor-pointer rounded-lg px-3 py-1 text-sm transition-all ${
                  view === tab.key
                    ? "bg-cyan-400/15 font-semibold text-cyan-300 ring-1 ring-cyan-400/40"
                    : "text-neutral-400 hover:bg-white/5 hover:text-neutral-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div
            onDragOver={(event: DragEvent<HTMLDivElement>) => event.preventDefault()}
            onDrop={(event: DragEvent<HTMLDivElement>) => {
              event.preventDefault();
              onUpload(event.dataTransfer.files?.[0]);
            }}
          >
            {data ? (
              <WaferCanvas
                imageUrl={png(data.image)}
                overlays={view === "detections" ? overlays : []}
                dots={view === "dots" ? data.dots : undefined}
                dimImage={view === "dots"}
                scanning={analysis.loading}
              />
            ) : (
              <div className="relative aspect-square w-full overflow-hidden rounded-full bg-neutral-900 ring-1 ring-cyan-400/25">
                {analysis.loading && (
                  <div className="absolute inset-x-[6%] h-0.5 animate-scan rounded-full bg-cyan-400/90 shadow-[0_0_14px_3px_rgba(34,211,238,0.75)]" />
                )}
              </div>
            )}
          </div>
          <p className={subtle}>Drop an image onto the wafer to analyze it, or pick one below.</p>
        </div>

        <div className={`${card} h-fit`}>
          <h3 className="text-sm font-semibold text-white">Radon sinogram</h3>
          {data ? (
            <img
              src={png(data.sinogram)}
              alt="radon sinogram"
              className="mt-2 w-full rounded-lg"
            />
          ) : (
            <div className="mt-2 aspect-[3/2] w-full animate-pulse rounded-lg bg-neutral-900" />
          )}
          <p className={`mt-2 ${subtle}`}>
            Radon transform of the defect dots — each column is one projection angle; bright sine
            traces reveal linear and radial structure.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <div className={card}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs tracking-wide text-neutral-400 uppercase">Attributed loss</p>
                <p className="text-3xl font-extrabold text-red-400 tabular-nums">
                  {dollars(lossValue)}
                </p>
              </div>
              <div>
                <p className="text-xs tracking-wide text-neutral-400 uppercase">Wafer yield</p>
                <p className="text-3xl font-extrabold text-emerald-400 tabular-nums">
                  {yieldValue.toFixed(1)}%
                </p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <MetricTile
                label="Failed dies"
                value={summary ? `${summary.failed_dies} / ${summary.gross_dies}` : "—"}
              />
              <MetricTile
                label="Top defect"
                value={topDefect ? topDefect.class : "none"}
                accent="text-cyan-300"
              />
            </div>
          </div>

          <div className={card}>
            <h3 className="text-sm font-semibold text-white">Model detections</h3>
            {data?.detections.length === 0 && (
              <p className={`mt-2 ${subtle}`}>No defects detected on this wafer.</p>
            )}
            <div className="mt-2 flex flex-col gap-1.5">
              {data?.detections.map((detection, index) => (
                <button
                  key={`${detection.class}-${index}`}
                  onClick={() => toggleHidden(index)}
                  className={`flex cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-1.5 text-left text-sm transition-colors hover:border-cyan-400/50 ${
                    hidden.includes(index)
                      ? "border-white/5 text-neutral-600"
                      : "border-white/10 text-neutral-200"
                  }`}
                >
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: overlayColors[index % overlayColors.length] }}
                  />
                  {detection.class}
                  <span className="ml-auto text-xs text-neutral-400 tabular-nums">
                    {percent(detection.confidence)} · {dollars(detection.yield_loss.dollars)}
                  </span>
                </button>
              ))}
            </div>
            {data?.ground_truth && (
              <div className="mt-3 flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-neutral-500">ground truth:</span>
                {data.ground_truth.map((name, index) => (
                  <span key={`${name}-${index}`} className={chip}>
                    {name}
                  </span>
                ))}
              </div>
            )}
          </div>

          {data && data.detections.length > 0 && (
            <details className={card} open>
              <summary className={summaryTitle}>Diagnosis &amp; recommended actions</summary>
              <div className="mt-3 flex flex-col gap-3">
                {data.detections.map((detection, index) => (
                  <DiagnosisCard
                    key={`${detection.class}-${index}`}
                    detection={detection}
                    color={overlayColors[index % overlayColors.length]}
                  />
                ))}
              </div>
            </details>
          )}

          {data && summary && (
            <details className={card}>
              <summary className={summaryTitle}>Yield breakdown</summary>
              <div className="mt-3 flex flex-col gap-4">
                <div className="grid grid-cols-3 gap-3">
                  <MetricTile label="Random yield" value={percent(summary.yield_random)} />
                  <MetricTile
                    label="D0 / mm²"
                    value={summary.d0_per_mm2?.toExponential(2) ?? "n/a"}
                  />
                  <MetricTile label="Cluster α" value={summary.alpha?.toFixed(2) ?? "none"} />
                </div>
                <div>
                  <h4 className="mb-1 text-xs tracking-wide text-neutral-400 uppercase">
                    Radial fail rate
                  </h4>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={radialData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="bin" stroke="#525252" tick={{ fill: "#a3a3a3", fontSize: 11 }} />
                      <YAxis
                        stroke="#525252"
                        tick={{ fill: "#a3a3a3", fontSize: 11 }}
                        tickFormatter={(value: number) => percent(value)}
                      />
                      <Tooltip
                        formatter={(value) => percent(Number(value))}
                        contentStyle={chartTooltipStyle}
                      />
                      <Bar dataKey="rate" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <h4 className="mb-1 text-xs tracking-wide text-neutral-400 uppercase">
                    Zone yields
                  </h4>
                  {Object.entries(data.zones).map(([zone, value]) => (
                    <div key={zone} className="mb-2">
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
            </details>
          )}
        </div>
      </div>

      <section className={card}>
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-sm font-semibold text-white">Browse wafers</h3>
          <select
            value={category}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => setCategory(event.target.value)}
            className={select}
          >
            <option value="">all categories</option>
            {waferCategories.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          {gallery.error && <span className={errorText}>{gallery.error}</span>}
          <Link
            to="/explorer"
            className="ml-auto cursor-pointer text-sm text-cyan-300 transition-colors hover:text-cyan-200"
          >
            Open full explorer →
          </Link>
        </div>
        <div className="mt-3 flex gap-3 overflow-x-auto pb-1">
          {gallery.data?.items.map((item) => (
            <button
              key={item.stem}
              onClick={() => selectWafer(item.stem)}
              className={`w-24 shrink-0 cursor-pointer rounded-xl p-1.5 transition-all hover:bg-white/10 ${
                !file && item.stem === stem ? "bg-cyan-400/10 ring-1 ring-cyan-400/50" : ""
              }`}
            >
              <img
                src={waferImageUrl(item.stem)}
                alt={item.stem}
                loading="lazy"
                className="aspect-square w-full rounded-full border border-white/10"
              />
              <p className="mt-1 truncate text-center text-xs text-neutral-300">{item.category}</p>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Analyze;
