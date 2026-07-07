import PageHeader from "../components/PageHeader";
import { card, cardTitle, label, subtle } from "../ui";

interface ClassResult {
	name: string;
	box50: number;
	mask50: number;
	box5095: number;
	mask5095: number;
}

const headline = [
	{
		label: "Mask mAP50",
		value: "0.852",
		accent: "text-cyan-700 dark:text-cyan-300",
		hero: true,
	},
	{
		label: "Box mAP50",
		value: "0.909",
		accent: "text-neutral-900 dark:text-neutral-100",
		hero: false,
	},
	{
		label: "Mask mAP50-95",
		value: "0.632",
		accent: "text-neutral-900 dark:text-neutral-100",
		hero: false,
	},
	{
		label: "Box mAP50-95",
		value: "0.741",
		accent: "text-neutral-900 dark:text-neutral-100",
		hero: false,
	},
];

const subsets = [
	{
		name: "Full test split",
		detail: "87 wafers · all 21 classes",
		mask50: 0.852,
		box50: 0.909,
	},
	{
		name: "Multi-defect combos",
		detail: "wafers with 2–4 overlapping patterns",
		mask50: 0.686,
		box50: 0.782,
	},
	{
		name: "Tiny edge scratches",
		detail: "smallest defect size in the dataset",
		mask50: 0.995,
		box50: 0.995,
	},
];

const perClass: ClassResult[] = [
	{
		name: "bullseye",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.995,
		mask5095: 0.995,
	},
	{
		name: "gradient",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.987,
		mask5095: 0.995,
	},
	{
		name: "double_ring",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.895,
		mask5095: 0.829,
	},
	{
		name: "scratch",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.864,
		mask5095: 0.821,
	},
	{
		name: "half_wafer",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.807,
		mask5095: 0.791,
	},
	{
		name: "radial_spokes",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.864,
		mask5095: 0.768,
	},
	{
		name: "wedge",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.814,
		mask5095: 0.744,
	},
	{
		name: "crescent",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.785,
		mask5095: 0.687,
	},
	{
		name: "edge_scratch",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.799,
		mask5095: 0.663,
	},
	{
		name: "edge_ring",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.895,
		mask5095: 0.544,
	},
	{
		name: "slip_lines",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.618,
		mask5095: 0.521,
	},
	{
		name: "comet",
		box50: 0.995,
		mask50: 0.995,
		box5095: 0.678,
		mask5095: 0.478,
	},
	{
		name: "edge_loc",
		box50: 0.912,
		mask50: 0.912,
		box5095: 0.746,
		mask5095: 0.77,
	},
	{
		name: "shot_grid",
		box50: 0.912,
		mask50: 0.872,
		box5095: 0.306,
		mask5095: 0.257,
	},
	{
		name: "near_full",
		box50: 0.835,
		mask50: 0.835,
		box5095: 0.805,
		mask5095: 0.733,
	},
	{
		name: "center",
		box50: 0.795,
		mask50: 0.795,
		box5095: 0.662,
		mask5095: 0.637,
	},
	{
		name: "random",
		box50: 0.816,
		mask50: 0.745,
		box5095: 0.809,
		mask5095: 0.745,
	},
	{
		name: "lift_pin",
		box50: 0.705,
		mask50: 0.64,
		box5095: 0.434,
		mask5095: 0.386,
	},
	{
		name: "donut",
		box50: 0.855,
		mask50: 0.596,
		box5095: 0.783,
		mask5095: 0.495,
	},
	{ name: "loc", box50: 0.715, mask50: 0.517, box5095: 0.517, mask5095: 0.39 },
	{
		name: "swirl",
		box50: 0.61,
		mask50: 0.042,
		box5095: 0.492,
		mask5095: 0.011,
	},
];

const scoreText = (value: number): string => {
	if (value >= 0.9) {
		return "text-emerald-600 dark:text-emerald-400";
	}
	if (value >= 0.7) {
		return "text-cyan-700 dark:text-cyan-300";
	}
	if (value >= 0.4) {
		return "text-amber-600 dark:text-yellow-300";
	}
	return "text-red-600 dark:text-red-400";
};

const scoreBar = (value: number): string => {
	if (value >= 0.9) {
		return "bg-emerald-500 dark:bg-emerald-400";
	}
	if (value >= 0.7) {
		return "bg-cyan-500 dark:bg-cyan-400";
	}
	if (value >= 0.4) {
		return "bg-amber-500 dark:bg-yellow-400";
	}
	return "bg-red-500 dark:bg-red-400";
};

const Evaluation = () => {
	return (
		<div className="flex animate-fade-up flex-col gap-5">
			<PageHeader kicker="Model benchmarks" title="Evaluation Results" />

			<div className="grid grid-cols-2 gap-3 md:grid-cols-4">
				{headline.map(item => (
					<div
						key={item.label}
						className={`${card} ${item.hero ? "border-cyan-600/30 dark:border-cyan-400/25" : ""}`}>
						<p className={label}>{item.label}</p>
						<p
							className={`mt-1 font-mono text-3xl font-bold tracking-tight tabular-nums ${item.accent}`}>
							{item.value}
						</p>
					</div>
				))}
			</div>

			<div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
				<div className={card}>
					<h3 className={cardTitle}>The model, and why it is different</h3>
					<div className="mt-3 flex flex-col gap-3 text-sm leading-relaxed text-neutral-600 dark:text-neutral-300">
						<p>
							WaferDetect runs a{" "}
							<strong className="text-neutral-900 dark:text-white">
								YOLO26-seg
							</strong>{" "}
							instance-segmentation model: a single-pass, anchor-free detector
							whose backbone and feature pyramid feed heads that predict — for
							every defect on the wafer — a class, a confidence, a bounding box,
							and a full polygon mask assembled from shared mask prototypes. It
							was fine-tuned from COCO-pretrained weights on a dataset of 580
							real, annotated wafers. Inference takes a few milliseconds per
							wafer.
						</p>
						<p>
							Prior wafer-map work — the WM-811K lineage — treats the problem as{" "}
							<strong className="text-neutral-900 dark:text-white">
								whole-image, single-label classification
							</strong>
							: one wafer in, one pattern name out. That formulation has two
							structural limits. Real production wafers carry co-occurring
							defects, and a classifier can only ever name one of them; and a
							label carries no location, so nothing downstream can measure a
							defect's area, orientation, or cost.
						</p>
						<p>
							Segmentation removes both limits: every failure pattern on the
							wafer is found separately, named, and outlined with a polygon —
							which is exactly what the analytics layer consumes for scratch
							kinematics and per-defect dollar attribution. The multi-defect
							combo subset below is the direct evidence: our classical
							classification baseline (zone-density + Radon + SVM) scores{" "}
							<strong className="text-neutral-900 dark:text-white">
								0 by construction
							</strong>{" "}
							on combo wafers, while the detector reaches{" "}
							<strong className="text-neutral-900 dark:text-white">
								0.686 mask mAP50
							</strong>{" "}
							on the same wafers.
						</p>
					</div>
				</div>

				<div className="flex flex-col gap-4">
					<div className={card}>
						<h3 className={cardTitle}>Results by subset</h3>
						<div className="mt-3 flex flex-col gap-4">
							{subsets.map(subset => (
								<div key={subset.name}>
									<div className="flex items-baseline justify-between gap-2">
										<span className="text-sm text-neutral-800 dark:text-neutral-200">
											{subset.name}
										</span>
										<span className="font-mono text-[10px] text-neutral-500">
											{subset.detail}
										</span>
									</div>
									<div className="mt-1.5 flex flex-col gap-1.5">
										<div className="flex items-center gap-2">
											<span className="w-14 font-mono text-[10px] tracking-wider text-neutral-500 uppercase">
												mask
											</span>
											<div className="h-1.5 flex-1 rounded-full bg-neutral-900/10 dark:bg-white/10">
												<div
													className={`h-1.5 rounded-full ${scoreBar(subset.mask50)}`}
													style={{ width: `${subset.mask50 * 100}%` }}
												/>
											</div>
											<span
												className={`w-12 text-right font-mono text-xs tabular-nums ${scoreText(subset.mask50)}`}>
												{subset.mask50.toFixed(3)}
											</span>
										</div>
										<div className="flex items-center gap-2">
											<span className="w-14 font-mono text-[10px] tracking-wider text-neutral-500 uppercase">
												box
											</span>
											<div className="h-1.5 flex-1 rounded-full bg-neutral-900/10 dark:bg-white/10">
												<div
													className={`h-1.5 rounded-full ${scoreBar(subset.box50)}`}
													style={{ width: `${subset.box50 * 100}%` }}
												/>
											</div>
											<span
												className={`w-12 text-right font-mono text-xs tabular-nums ${scoreText(subset.box50)}`}>
												{subset.box50.toFixed(3)}
											</span>
										</div>
									</div>
								</div>
							))}
						</div>
					</div>

					<div className={card}>
						<h3 className={cardTitle}>Evaluation setup</h3>
						<ul className="mt-3 flex list-disc flex-col gap-1.5 pl-4 text-sm leading-relaxed text-neutral-600 marker:text-cyan-600/60 dark:text-neutral-300 dark:marker:text-cyan-400/60">
							<li>
								Frozen, stratified 87-wafer test split (seed 42) — never used
								for training or tuning.
							</li>
							<li>
								COCO-style mean average precision at IoU 0.50 (mAP50) and
								averaged over IoU 0.50–0.95 (mAP50-95), for both boxes and
								masks.
							</li>
							<li>
								Combo subset: only wafers with 2–4 overlapping defect patterns —
								the case single-label classifiers cannot express.
							</li>
						</ul>
					</div>
				</div>
			</div>

			<div className={card}>
				<h3 className={cardTitle}>Per-class results</h3>
				<p className={`mt-1 ${subtle}`}>
					Full test split, sorted by mask mAP50. Thin, non-convex shapes (swirl)
					are the known hard case for mask IoU.
				</p>
				<div className="mt-3 overflow-x-auto">
					<table className="w-full min-w-140 text-sm">
						<thead>
							<tr className="border-b border-neutral-900/10 text-left font-mono text-[10px] tracking-[0.14em] text-neutral-500 uppercase dark:border-white/10">
								<th className="py-2 pr-3 font-medium">Class</th>
								<th className="py-2 pr-3 font-medium">Mask AP50</th>
								<th className="w-1/3 py-2 pr-3 font-medium" />
								<th className="py-2 pr-3 font-medium">Box AP50</th>
								<th className="py-2 pr-3 font-medium">Mask AP50-95</th>
								<th className="py-2 font-medium">Box AP50-95</th>
							</tr>
						</thead>
						<tbody>
							{perClass.map(row => (
								<tr
									key={row.name}
									className="border-b border-neutral-900/5 transition-colors hover:bg-neutral-900/3 dark:border-white/5 dark:hover:bg-white/5">
									<td className="py-2 pr-3 font-mono text-xs font-medium text-neutral-800 dark:text-neutral-200">
										{row.name}
									</td>
									<td
										className={`py-2 pr-3 font-mono text-xs font-semibold tabular-nums ${scoreText(row.mask50)}`}>
										{row.mask50.toFixed(3)}
									</td>
									<td className="py-2 pr-3">
										<div className="h-1.5 w-full rounded-full bg-neutral-900/10 dark:bg-white/10">
											<div
												className={`h-1.5 rounded-full ${scoreBar(row.mask50)}`}
												style={{ width: `${row.mask50 * 100}%` }}
											/>
										</div>
									</td>
									<td className="py-2 pr-3 font-mono text-xs text-neutral-600 tabular-nums dark:text-neutral-300">
										{row.box50.toFixed(3)}
									</td>
									<td className="py-2 pr-3 font-mono text-xs text-neutral-500 tabular-nums dark:text-neutral-400">
										{row.mask5095.toFixed(3)}
									</td>
									<td className="py-2 font-mono text-xs text-neutral-500 tabular-nums dark:text-neutral-400">
										{row.box5095.toFixed(3)}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
};

export default Evaluation;
