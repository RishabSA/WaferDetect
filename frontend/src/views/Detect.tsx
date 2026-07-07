import type { ChangeEvent, DragEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
	FaFileExport,
	FaFilePdf,
	FaImage,
	FaInfoCircle,
	FaUpload,
} from "react-icons/fa";
import { Link, useSearchParams } from "react-router";
import {
	Bar,
	BarChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

import type { AnalyzeResponse } from "../api";
import { api, useApi, waferCategories, waferImageUrl } from "../api";
import DiagnosisCard from "../components/DiagnosisCard";
import InfoModal from "../components/InfoModal";
import MetricTile from "../components/MetricTile";
import PageHeader from "../components/PageHeader";
import { overlayColors, WaferCanvas } from "../components/WaferCanvas";
import { dollars, percent, png } from "../format";
import { useIsDark } from "../theme";
import {
	buttonGhost,
	buttonPrimary,
	card,
	cardTitle,
	chartTheme,
	chip,
	errorText,
	input,
	label,
	segmented,
	segmentedItem,
	select,
	subtle,
} from "../ui";
import useCountUp from "../useCountUp";
import useDebounced from "../useDebounced";

const demoStem = "0487_combo_random+edge_loc+comet";
const galleryLimit = 14;
// wafer disc fraction of the image — matches wafer_frac in scripts/datagen/generator.py
const waferFrac = 0.97;
const waferPngScale = 2;
const waferPresets = [50, 75, 100, 150, 225];
const dieMmMin = 3;
const dieMmMax = 20;
const typicalWaferValueMin = 2000;
const typicalWaferValueMax = 500000;

const viewTabs = [
	{ key: "detections", label: "Detections" },
	{ key: "dots", label: "Defect dots" },
	{ key: "sinogram", label: "Radon sinogram" },
] as const;
type ViewKey = (typeof viewTabs)[number]["key"];

const summaryTitle =
	"cursor-pointer text-xs font-semibold tracking-[0.14em] text-neutral-700 uppercase select-none marker:text-cyan-600 dark:text-neutral-200 dark:marker:text-cyan-400";

const downloadBlob = (blob: Blob, filename: string) => {
	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = filename;
	link.click();
	URL.revokeObjectURL(url);
};

// stepper-style alignment marks framing the wafer stage
const stageBrackets = (
	<>
		<span className="pointer-events-none absolute top-0 left-0 h-5 w-5 border-t border-l border-cyan-600/40 dark:border-cyan-400/40" />
		<span className="pointer-events-none absolute top-0 right-0 h-5 w-5 border-t border-r border-cyan-600/40 dark:border-cyan-400/40" />
		<span className="pointer-events-none absolute bottom-0 left-0 h-5 w-5 border-b border-l border-cyan-600/40 dark:border-cyan-400/40" />
		<span className="pointer-events-none absolute right-0 bottom-0 h-5 w-5 border-r border-b border-cyan-600/40 dark:border-cyan-400/40" />
	</>
);

const Detect = () => {
	const [searchParams, setSearchParams] = useSearchParams();
	const stem = searchParams.get("stem") ?? demoStem;
	const [file, setFile] = useState<File | null>(null);
	const [view, setView] = useState<ViewKey>("detections");
	const [hidden, setHidden] = useState<number[]>([]);
	const [category, setCategory] = useState("");
	const [waferPreset, setWaferPreset] = useState("150");
	const [customRadiusInput, setCustomRadiusInput] = useState("150");
	const [customRadius, setCustomRadius] = useState(150);
	const [dieMm, setDieMm] = useState(6);
	const [dieValueInput, setDieValueInput] = useState("25");
	const [dieValue, setDieValue] = useState(25);
	const [showSinogramInfo, setShowSinogramInfo] = useState(false);
	const [exporting, setExporting] = useState<"" | "pdf" | "klarf">("");
	const [exportError, setExportError] = useState("");
	const fileRef = useRef<HTMLInputElement>(null);
	const isDark = useIsDark();
	const chart = chartTheme(isDark);

	const waferRadius =
		waferPreset === "other" ? customRadius : Number(waferPreset);
	const dieMmDebounced = useDebounced(dieMm);
	const dieValueDebounced = useDebounced(dieValue);
	const waferRadiusDebounced = useDebounced(waferRadius);

	const analysis = useApi<AnalyzeResponse>(() => {
		const params = {
			die_mm: dieMmDebounced,
			die_value: dieValueDebounced,
			wafer_radius_mm: waferRadiusDebounced,
		};
		return file ? api.analyzeFile(file, params) : api.analyze(stem, params);
	}, [stem, file, dieMmDebounced, dieValueDebounced, waferRadiusDebounced]);
	const gallery = useApi(
		() => api.wafers({ category, limit: galleryLimit }),
		[category],
	);

	useEffect(() => setHidden([]), [analysis.data]);

	// useApi keeps the previous response while a new request is in flight; record
	// which wafer produced the loaded data so a newly picked wafer shows its own
	// raw image (not the previous result) while YOLO runs
	const loadedFor = useRef<{ stem: string; file: File | null }>({
		stem: "",
		file: null,
	});
	useEffect(() => {
		if (analysis.data) {
			loadedFor.current = { stem, file };
		}
	}, [analysis.data]);

	// A KLARF upload carries its own die pitch and wafer size — apply them to
	// the what-if controls once per file, leaving later manual tweaks alone.
	// Runs after the loadedFor effect so the currency check sees fresh data.
	const klarfApplied = useRef<File | null>(null);
	useEffect(() => {
		const meta = analysis.data?.klarf;
		if (
			!file ||
			!meta ||
			loadedFor.current.file !== file ||
			klarfApplied.current === file
		) {
			return;
		}
		klarfApplied.current = file;

		setDieMm(Math.min(dieMmMax, Math.max(dieMmMin, meta.die_mm)));
		if (waferPresets.includes(meta.wafer_radius_mm)) {
			setWaferPreset(String(meta.wafer_radius_mm));
		} else {
			setWaferPreset("other");
			setCustomRadiusInput(String(meta.wafer_radius_mm));
			setCustomRadius(meta.wafer_radius_mm);
		}
	}, [analysis.data, file]);

	const uploadPreview = useMemo(
		() => (file ? URL.createObjectURL(file) : ""),
		[file],
	);
	useEffect(
		() => () => {
			if (uploadPreview) {
				URL.revokeObjectURL(uploadPreview);
			}
		},
		[uploadPreview],
	);

	const data = analysis.data;
	const dataIsCurrent =
		data !== null &&
		loadedFor.current.stem === stem &&
		loadedFor.current.file === file;
	// A KLARF upload has no pixels to preview — the wafer map arrives rendered
	// in the analysis response
	const previewUrl = file
		? file.type.startsWith("image/")
			? uploadPreview
			: ""
		: waferImageUrl(stem);
	const summary = data?.wafer_summary;
	const lossValue = useCountUp(summary?.total_loss_dollars ?? 0);
	const yieldValue = useCountUp((summary?.yield ?? 0) * 100);

	const goodDies = summary ? summary.gross_dies - summary.failed_dies : null;
	const impliedWaferValue = goodDies === null ? null : goodDies * dieValue;
	const valueWarning =
		impliedWaferValue !== null &&
		(impliedWaferValue < typicalWaferValueMin ||
			impliedWaferValue > typicalWaferValueMax);

	const selectWafer = (nextStem: string) => {
		setFile(null);
		setSearchParams({ stem: nextStem });
	};

	const onUpload = (nextFile: File | undefined) => {
		if (nextFile) {
			setFile(nextFile);
		}
	};

	const onExport = async (kind: "pdf" | "klarf") => {
		setExporting(kind);
		setExportError("");
		try {
			const params = {
				die_mm: dieMmDebounced,
				die_value: dieValueDebounced,
				wafer_radius_mm: waferRadiusDebounced,
			};
			const exporters = {
				pdf: () =>
					file ? api.reportFile(file, params) : api.report(stem, params),
				klarf: () =>
					file ? api.klarfFile(file, params) : api.klarf(stem, params),
			};
			const blob = await exporters[kind]();

			const base = file ? file.name.replace(/\.[^.]+$/, "") : stem;
			downloadBlob(blob, `waferdetect_${base}.${kind}`);
		} catch (cause) {
			setExportError((cause as Error).message);
		} finally {
			setExporting("");
		}
	};

	const onDownloadWafer = () => {
		if (!data) {
			return;
		}

		const image = new Image();
		image.onload = () => {
			const width = image.naturalWidth * waferPngScale;
			const height = image.naturalHeight * waferPngScale;
			const canvas = document.createElement("canvas");
			canvas.width = width;
			canvas.height = height;
			const context = canvas.getContext("2d");
			if (!context) {
				return;
			}

			// Clip to the wafer disc (+2 px keeps the drawn outline); everything
			// outside the circle stays transparent
			const radius =
				(Math.min(width, height) * waferFrac) / 2 + 2 * waferPngScale;
			context.beginPath();
			context.arc(width / 2, height / 2, radius, 0, Math.PI * 2);
			context.clip();
			context.drawImage(image, 0, 0, width, height);

			for (const overlay of overlays) {
				if (!overlay.visible || overlay.points.length < 3) {
					continue;
				}
				context.beginPath();
				overlay.points.forEach(([x, y], index) =>
					index === 0
						? context.moveTo(x * width, y * height)
						: context.lineTo(x * width, y * height),
				);
				context.closePath();
				context.fillStyle = overlay.color;
				context.strokeStyle = overlay.color;
				context.lineWidth = width * 0.005;
				context.globalAlpha = 0.14;
				context.fill();
				context.globalAlpha = 1;
				context.stroke();
			}

			canvas.toBlob(blob => {
				if (blob) {
					const base = file ? file.name.replace(/\.[^.]+$/, "") : stem;
					downloadBlob(blob, `waferdetect_${base}_detections.png`);
				}
			}, "image/png");
		};
		image.onerror = () =>
			setExportError("Could not decode the wafer image for PNG export");
		image.src = png(data.image);
	};

	const onDieValue = (event: ChangeEvent<HTMLInputElement>) => {
		setDieValueInput(event.target.value);
		const next = Number(event.target.value);
		if (Number.isFinite(next) && next > 0) {
			setDieValue(next);
		}
	};

	const onCustomRadius = (event: ChangeEvent<HTMLInputElement>) => {
		setCustomRadiusInput(event.target.value);
		const next = Number(event.target.value);
		if (Number.isFinite(next) && next > 0) {
			setCustomRadius(next);
		}
	};

	const toggleHidden = (index: number) =>
		setHidden(
			hidden.includes(index)
				? hidden.filter(item => item !== index)
				: [...hidden, index],
		);

	const topDefect = data?.detections.length
		? [...data.detections].sort(
				(a, b) => b.yield_loss.dollars - a.yield_loss.dollars,
			)[0]
		: null;

	const overlays = (data?.detections ?? []).map((detection, index) => ({
		points: detection.polygon,
		label: detection.class,
		color: overlayColors[index % overlayColors.length],
		visible: !hidden.includes(index),
	}));

	const radialData = (data?.radial ?? []).map((rate, index) => ({
		bin: `r${index}`,
		rate,
	}));

	return (
		<div className="flex animate-fade-up flex-col gap-5">
			<PageHeader kicker="Wafer inspection" title="Detect">
				<span className={chip}>{file ? file.name : stem}</span>
				{analysis.loading && (
					<span className="flex items-center gap-1.5 font-mono text-[11px] tracking-[0.18em] text-cyan-700 uppercase dark:text-cyan-300">
						<span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-600 dark:bg-cyan-400" />
						Analyzing
					</span>
				)}
			</PageHeader>

			{analysis.error && (
				<p className={errorText}>
					{analysis.error}
					{analysis.error.includes("503") &&
						" — start the API with --model-path to enable analysis."}
				</p>
			)}
			{exportError && <p className={errorText}>{exportError}</p>}

			<div className="grid gap-5 lg:grid-cols-[minmax(0,11fr)_minmax(0,9fr)]">
				<div className="flex flex-col gap-3">
					<div className="flex flex-wrap items-center gap-2">
						<div className={segmented}>
							{viewTabs.map(tab => (
								<button
									key={tab.key}
									onClick={() => setView(tab.key)}
									className={segmentedItem(view === tab.key)}>
									{tab.label}
								</button>
							))}
						</div>
						<input
							ref={fileRef}
							type="file"
							accept="image/*,.klarf"
							className="hidden"
							onChange={(event: ChangeEvent<HTMLInputElement>) =>
								onUpload(event.target.files?.[0])
							}
						/>
						<button
							onClick={() => fileRef.current?.click()}
							title="Upload a wafer map image or a KLARF defect file"
							className={`ml-auto ${buttonPrimary}`}>
							<span className="flex items-center gap-2">
								<FaUpload size={12} />
								Upload image / KLARF
							</span>
						</button>
					</div>

					<div className="flex flex-wrap items-center justify-end gap-2">
							<button
								onClick={onDownloadWafer}
								disabled={!data || !dataIsCurrent}
								title="Download the annotated wafer as a PNG with a transparent background — visible detections only"
								className={buttonGhost}>
								<span className="flex items-center gap-2">
									<FaImage size={12} />
									Export detections
								</span>
							</button>
							<button
								onClick={() => onExport("klarf")}
								disabled={!data || !dataIsCurrent || exporting !== ""}
								title="Export the detections as a KLARF defect file — the industry-standard format emitted by fab inspection tools"
								className={buttonGhost}>
								<span className="flex items-center gap-2">
									<FaFileExport size={12} />
									{exporting === "klarf" ? "Writing…" : "Export KLARF"}
								</span>
							</button>
							<button
								onClick={() => onExport("pdf")}
								disabled={!data || !dataIsCurrent || exporting !== ""}
								title="Download a PDF report of the full analysis"
								className={buttonGhost}>
								<span className="flex items-center gap-2">
									<FaFilePdf size={12} />
									{exporting === "pdf" ? "Rendering…" : "Export report"}
								</span>
							</button>
						</div>

					<div
						onDragOver={(event: DragEvent<HTMLDivElement>) =>
							event.preventDefault()
						}
						onDrop={(event: DragEvent<HTMLDivElement>) => {
							event.preventDefault();
							onUpload(event.dataTransfer.files?.[0]);
						}}>
						{view === "sinogram" ? (
							<div className={card}>
								<div className="flex items-center justify-between">
									<h3 className={cardTitle}>Radon sinogram</h3>
									<button
										onClick={() => setShowSinogramInfo(true)}
										aria-label="About the Radon sinogram"
										className="cursor-pointer rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-neutral-900/5 hover:text-cyan-700 dark:text-neutral-400 dark:hover:bg-white/5 dark:hover:text-cyan-300">
										<FaInfoCircle size={14} />
									</button>
								</div>
								{data && dataIsCurrent ? (
									<img
										src={png(data.sinogram)}
										alt="radon sinogram"
										className="mt-2 w-full rounded-lg"
									/>
								) : (
									<div className="mt-2 aspect-3/2 w-full animate-pulse rounded-lg bg-inset" />
								)}
							</div>
						) : (
							<div className="relative p-3">
								{stageBrackets}
								{data && dataIsCurrent ? (
									<WaferCanvas
										imageUrl={png(data.image)}
										overlays={view === "detections" ? overlays : []}
										dots={view === "dots" ? data.dots : undefined}
										dimImage={view === "dots"}
										scanning={analysis.loading}
									/>
								) : previewUrl ? (
									<WaferCanvas
										imageUrl={previewUrl}
										overlays={[]}
										scanning={analysis.loading}
									/>
								) : (
									<div className="aspect-square w-full animate-pulse rounded-full bg-neutral-900/5 dark:bg-white/5" />
								)}
							</div>
						)}
					</div>
					<p className={subtle}>
						Drop a wafer image or KLARF defect file onto the wafer to analyze
						it, or pick one below.
					</p>

					<div className={card}>
						<div className="flex flex-wrap items-center gap-3">
							<h3 className={cardTitle}>Browse wafers</h3>
							<select
								value={category}
								onChange={(event: ChangeEvent<HTMLSelectElement>) =>
									setCategory(event.target.value)
								}
								className={select}>
								<option value="">all categories</option>
								{waferCategories.map(value => (
									<option key={value} value={value}>
										{value}
									</option>
								))}
							</select>
							{gallery.error && (
								<span className={errorText}>{gallery.error}</span>
							)}
							<Link
								to="/explorer"
								className="ml-auto cursor-pointer text-sm text-cyan-700 transition-colors hover:text-cyan-600 dark:text-cyan-300 dark:hover:text-cyan-200">
								Open full explorer →
							</Link>
						</div>
						<div className="mt-3 flex gap-3 overflow-x-auto pb-1">
							{gallery.loading &&
								!gallery.data &&
								Array.from({ length: 8 }, (_, index) => (
									<div key={index} className="w-24 shrink-0 p-1.5">
										<div className="aspect-square w-full animate-pulse rounded-full bg-neutral-900/5 dark:bg-white/5" />
										<div className="mx-auto mt-2 h-2.5 w-14 animate-pulse rounded bg-neutral-900/5 dark:bg-white/5" />
									</div>
								))}
							{gallery.data?.items.map(item => (
								<button
									key={item.stem}
									onClick={() => selectWafer(item.stem)}
									className={`w-24 shrink-0 cursor-pointer rounded-xl p-1.5 transition-all hover:bg-neutral-900/5 dark:hover:bg-white/10 ${
										!file && item.stem === stem
											? "bg-cyan-500/10 ring-1 ring-cyan-600/50 dark:bg-cyan-400/10 dark:ring-cyan-400/50"
											: ""
									}`}>
									<img
										src={waferImageUrl(item.stem)}
										alt={item.stem}
										loading="lazy"
										className="aspect-square w-full rounded-full border border-neutral-900/10 dark:border-white/10"
									/>
									<p className="mt-1 truncate text-center font-mono text-[10px] text-neutral-500 dark:text-neutral-400">
										{item.category}
									</p>
								</button>
							))}
						</div>
					</div>
				</div>

				<div className="flex flex-col gap-4">
					<div className={card}>
						<div className="grid grid-cols-2">
							<div className="pr-4">
								<p className={label}>Attributed loss</p>
								<p className="mt-1 font-mono text-3xl font-bold tracking-tight text-red-600 tabular-nums md:text-4xl dark:text-red-400">
									{dollars(lossValue)}
								</p>
							</div>
							<div className="border-l border-neutral-900/10 pl-4 dark:border-white/8">
								<p className={label}>Wafer yield</p>
								<p className="mt-1 font-mono text-3xl font-bold tracking-tight text-emerald-600 tabular-nums md:text-4xl dark:text-emerald-400">
									{yieldValue.toFixed(1)}%
								</p>
							</div>
						</div>
						<div className="mt-4 grid grid-cols-2 gap-3">
							<MetricTile
								label="Failed dies"
								value={
									summary
										? `${summary.failed_dies} / ${summary.gross_dies}`
										: "—"
								}
							/>
							<MetricTile
								label="Top defect"
								value={topDefect ? topDefect.class : "none"}
								accent="text-cyan-700 dark:text-cyan-300"
							/>
						</div>
					</div>

					<div className={card}>
						<h3 className={cardTitle}>What-if parameters</h3>
						<div className="mt-3 flex flex-col gap-3">
							<label className={`flex flex-col gap-1.5 ${label}`}>
								Wafer size
								<select
									value={waferPreset}
									onChange={(event: ChangeEvent<HTMLSelectElement>) =>
										setWaferPreset(event.target.value)
									}
									className={select}>
									{waferPresets.map(radius => (
										<option key={radius} value={String(radius)}>
											{radius} mm radius ({radius * 2} mm diameter)
										</option>
									))}
									<option value="other">Other…</option>
								</select>
							</label>
							{waferPreset === "other" && (
								<label className={`flex flex-col gap-1.5 ${label}`}>
									Custom radius (mm)
									<input
										type="number"
										value={customRadiusInput}
										min={10}
										step={5}
										onChange={onCustomRadius}
										className={`font-mono tabular-nums ${input}`}
									/>
								</label>
							)}
							<label className={`flex flex-col gap-1.5 ${label}`}>
								<span>
									Die size —{" "}
									<span className="text-cyan-700 dark:text-cyan-300">
										{dieMm.toFixed(1)} mm
									</span>
								</span>
								<input
									type="range"
									min={dieMmMin}
									max={dieMmMax}
									step={0.5}
									value={dieMm}
									onChange={(event: ChangeEvent<HTMLInputElement>) =>
										setDieMm(Number(event.target.value))
									}
									className="w-full cursor-pointer accent-cyan-600 dark:accent-cyan-400"
								/>
							</label>
							<label className={`flex flex-col gap-1.5 ${label}`}>
								Value per good die ($)
								<input
									type="number"
									value={dieValueInput}
									min={0}
									step={1}
									onChange={onDieValue}
									className={`font-mono tabular-nums ${input}`}
								/>
							</label>
							{valueWarning && impliedWaferValue !== null && (
								<p className="text-xs leading-relaxed text-amber-600 dark:text-yellow-300">
									At {dollars(dieValue)} per die this wafer is worth ~
									{dollars(impliedWaferValue)} — outside the typical{" "}
									{dollars(typicalWaferValueMin)}–
									{dollars(typicalWaferValueMax)} range for a production wafer.
								</p>
							)}
						</div>
					</div>

					<div className={card}>
						<h3 className={cardTitle}>Model detections</h3>
						{data?.detections.length === 0 && (
							<p className={`mt-2 ${subtle}`}>
								No defects detected on this wafer.
							</p>
						)}
						<div className="mt-2 flex flex-col gap-1.5">
							{data?.detections.map((detection, index) => (
								<button
									key={`${detection.class}-${index}`}
									onClick={() => toggleHidden(index)}
									className={`flex cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-1.5 text-left text-sm transition-colors hover:border-cyan-600/50 dark:hover:border-cyan-400/50 ${
										hidden.includes(index)
											? "border-neutral-900/5 text-neutral-400 dark:border-white/5 dark:text-neutral-600"
											: "border-neutral-900/10 bg-neutral-900/2 text-neutral-700 dark:border-white/10 dark:bg-white/2 dark:text-neutral-200"
									}`}>
									<span
										className="h-2.5 w-2.5 shrink-0 rounded-full"
										style={{
											backgroundColor:
												overlayColors[index % overlayColors.length],
										}}
									/>
									{detection.class}
									<span className="ml-auto font-mono text-[11px] text-neutral-500 tabular-nums dark:text-neutral-400">
										{percent(detection.confidence)} ·{" "}
										{dollars(detection.yield_loss.dollars)}
									</span>
								</button>
							))}
						</div>
						{data?.ground_truth && (
							<div className="mt-3 flex flex-wrap items-center gap-1.5">
								<span className={label}>ground truth</span>
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
							<summary className={summaryTitle}>
								Diagnosis &amp; recommended actions
							</summary>
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
									<MetricTile
										label="Random yield"
										value={percent(summary.yield_random)}
									/>
									<MetricTile
										label="D0 / mm²"
										value={summary.d0_per_mm2?.toExponential(2) ?? "n/a"}
									/>
									<MetricTile
										label="Cluster α"
										value={summary.alpha?.toFixed(2) ?? "none"}
									/>
								</div>
								<div>
									<h4 className={`mb-1 ${label}`}>Radial fail rate</h4>
									<ResponsiveContainer width="100%" height={180}>
										<BarChart data={radialData}>
											<CartesianGrid
												strokeDasharray="3 3"
												stroke={chart.grid}
											/>
											<XAxis
												dataKey="bin"
												stroke={chart.axis}
												tick={chart.tick}
											/>
											<YAxis
												stroke={chart.axis}
												tick={chart.tick}
												tickFormatter={(value: number) => percent(value)}
											/>
											<Tooltip
												formatter={value => percent(Number(value))}
												contentStyle={chart.tooltip}
											/>
											<Bar
												dataKey="rate"
												fill={chart.bar}
												radius={[4, 4, 0, 0]}
											/>
										</BarChart>
									</ResponsiveContainer>
								</div>
								<div>
									<h4 className={`mb-1 ${label}`}>Zone yields</h4>
									{Object.entries(data.zones).map(([zone, value]) => (
										<div key={zone} className="mb-2">
											<div className="flex justify-between text-sm text-neutral-600 dark:text-neutral-300">
												<span>{zone}</span>
												<span className="font-mono text-xs tabular-nums">
													{percent(value)}
												</span>
											</div>
											<div className="h-1.5 rounded-full bg-neutral-900/10 dark:bg-white/10">
												<div
													className="h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400"
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

			{showSinogramInfo && (
				<InfoModal
					title="Radon sinogram"
					onClose={() => setShowSinogramInfo(false)}>
					<p>
						The Radon transform projects the wafer's defect dots onto a line
						from every direction: each column of the sinogram is one projection
						angle (0–180°), and each row is a position along that line.
					</p>
					<p>
						Structure that is hard to see in the raw map jumps out here: a
						straight scratch collapses into a single bright spot at its angle,
						radial spokes repeat as evenly spaced peaks, and rings spread into
						broad symmetric bands. Random background dots stay diffuse.
					</p>
					<p>
						Rotating the wafer only shifts the pattern sideways, which makes
						Radon features rotation-invariant — the same trick the original
						WM-811K paper used to classify real fab wafer maps.
					</p>
				</InfoModal>
			)}
		</div>
	);
};

export default Detect;
