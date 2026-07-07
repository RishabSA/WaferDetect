import { useEffect, useState, type DependencyList } from "react";

export interface WaferItem {
	stem: string;
	category: string;
	split: string;
}

export interface WaferList {
	total: number;
	items: WaferItem[];
}

export interface WaferInstance {
	class: string;
	vertices: number;
}

export interface WaferDetail {
	stem: string;
	category: string;
	split: string;
	instances: WaferInstance[];
}

export interface YieldLoss {
	dies: number;
	failed: number;
	excess_failed: number;
	yield_loss_frac: number;
	dollars: number;
}

export interface KnowledgeEntry {
	mechanism: string;
	process_steps: string[];
	tool_families: string[];
	severity_weight: number;
	action: string;
}

export interface Kinematics {
	verdict: string;
	orientation_deg: number;
	radius_of_curvature: number | null;
	arc_center?: [number, number] | null;
	entry_bearing_deg: number | null;
}

export interface DiagnosisDetection {
	class: string;
	confidence: number;
	geometry: { area_frac: number; centroid_r: number };
	yield_loss: YieldLoss;
	diagnosis: KnowledgeEntry;
	kinematics?: Kinematics;
}

export interface WaferSummary {
	gross_dies: number;
	failed_dies: number;
	yield: number;
	d0_per_mm2: number | null;
	alpha: number | null;
	yield_random: number;
	total_loss_dollars: number;
}

export interface YieldPanel {
	summary: WaferSummary;
	radial: number[];
	zones: { center: number; mid: number; edge: number };
	regions: YieldLoss[];
}

export interface AnalyzeDetection extends DiagnosisDetection {
	polygon: [number, number][];
}

export interface AnalyzeParams {
	die_mm: number;
	die_value: number;
	wafer_radius_mm: number;
}

export interface KlarfMeta {
	die_mm: number;
	wafer_radius_mm: number;
	wafer_id: string;
	classes: string[];
}

export interface AnalyzeResponse {
	stem: string | null;
	image: string;
	dots: [number, number][];
	sinogram: string;
	detections: AnalyzeDetection[];
	wafer_summary: WaferSummary;
	radial: number[];
	zones: { center: number; mid: number; edge: number };
	ground_truth: string[] | null;
	klarf: KlarfMeta | null;
}

export interface ParetoResponse {
	wafers: number;
	pareto: [string, number][];
}

export interface ThermalResponse {
	temperature: string;
	stress: string;
	slip_probability: string;
	sample: string;
	stats: { min_temperature: number; max_temperature: number };
}

export interface FieldResponse {
	probability: string;
	sample: string;
}

export interface ShotGridVerdict {
	verdict: string;
	intra_max_z: number;
	intra_position?: [number, number];
	shot_max_z: number;
	shot_position?: [number, number];
}

export interface ShotGridResponse {
	field: string;
	sample: string;
	verdict: ShotGridVerdict;
}

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
	const response = await fetch(path, init);
	if (!response.ok) {
		throw new Error(
			`${init?.method ?? "GET"} ${path} failed (${response.status}): ${await response.text()}`,
		);
	}

	return response.json() as Promise<T>;
};

const requestBlob = async (path: string, init?: RequestInit): Promise<Blob> => {
	const response = await fetch(path, init);
	if (!response.ok) {
		throw new Error(
			`${init?.method ?? "GET"} ${path} failed (${response.status}): ${await response.text()}`,
		);
	}

	return response.blob();
};

const analyzeQuery = (params: AnalyzeParams): string =>
	new URLSearchParams({
		die_mm: String(params.die_mm),
		die_value: String(params.die_value),
		wafer_radius_mm: String(params.wafer_radius_mm),
	}).toString();

const postJson = <T>(path: string, body: unknown): Promise<T> =>
	request<T>(path, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	});

export const api = {
	wafers: (params: {
		split?: string;
		category?: string;
		offset?: number;
		limit?: number;
	}) => {
		const entries = Object.entries(params)
			.filter(([, value]) => value !== undefined && value !== "")
			.map(([key, value]) => [key, String(value)]);
		const query = new URLSearchParams(entries);
		return request<WaferList>(`/api/wafers?${query}`);
	},
	waferDetail: (stem: string) =>
		request<WaferDetail>(`/api/wafers/${encodeURIComponent(stem)}`),
	analyze: (stem: string, params: AnalyzeParams) =>
		request<AnalyzeResponse>(
			`/api/analyze?stem=${encodeURIComponent(stem)}&${analyzeQuery(params)}`,
			{ method: "POST" },
		),
	analyzeFile: (file: File, params: AnalyzeParams) => {
		const body = new FormData();
		body.append("file", file);
		return request<AnalyzeResponse>(`/api/analyze?${analyzeQuery(params)}`, {
			method: "POST",
			body,
		});
	},
	klarf: (stem: string, params: AnalyzeParams) =>
		requestBlob(
			`/api/klarf?stem=${encodeURIComponent(stem)}&${analyzeQuery(params)}`,
			{ method: "POST" },
		),
	klarfFile: (file: File, params: AnalyzeParams) => {
		const body = new FormData();
		body.append("file", file);
		return requestBlob(`/api/klarf?${analyzeQuery(params)}`, {
			method: "POST",
			body,
		});
	},
	report: (stem: string, params: AnalyzeParams) =>
		requestBlob(
			`/api/report?stem=${encodeURIComponent(stem)}&${analyzeQuery(params)}`,
			{ method: "POST" },
		),
	reportFile: (file: File, params: AnalyzeParams) => {
		const body = new FormData();
		body.append("file", file);
		return requestBlob(`/api/report?${analyzeQuery(params)}`, {
			method: "POST",
			body,
		});
	},
	yieldWafer: (stem: string) =>
		request<YieldPanel>(`/api/yield/wafer/${encodeURIComponent(stem)}`),
	pareto: (split: string, limit: number) =>
		request<ParetoResponse>(`/api/yield/pareto?split=${split}&limit=${limit}`),
	thermal: (body: Record<string, number | null>) =>
		postJson<ThermalResponse>("/api/physics/thermal", body),
	spincoat: (body: { mode: string; seed: number }) =>
		postJson<FieldResponse>("/api/physics/spincoat", body),
	cmp: (body: { mode: string; seed: number }) =>
		postJson<FieldResponse>("/api/physics/cmp", body),
	shotgrid: (body: { mode: string; seed: number }) =>
		postJson<ShotGridResponse>("/api/physics/shotgrid", body),
};

export const waferImageUrl = (stem: string): string =>
	`/api/wafers/${encodeURIComponent(stem)}/image`;

export const waferCategories = [
	"center",
	"donut",
	"edge_ring",
	"edge_loc",
	"scratch",
	"random",
	"loc",
	"near_full",
	"swirl",
	"radial_spokes",
	"shot_grid",
	"crescent",
	"half_wafer",
	"wedge",
	"comet",
	"edge_scratch_tiny",
	"edge_scratch_small",
	"edge_scratch_medium",
	"edge_scratch_large",
	"lift_pin",
	"bullseye",
	"gradient",
	"slip_lines",
	"double_ring",
	"combo",
];

export const useApi = <T>(
	loader: () => Promise<T>,
	deps: DependencyList,
): { data: T | null; error: string; loading: boolean } => {
	const [data, setData] = useState<T | null>(null);
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		let cancelled = false;
		setLoading(true);
		setError("");
		loader()
			.then(result => {
				if (!cancelled) {
					setData(result);
				}
			})
			.catch((cause: Error) => {
				if (!cancelled) {
					setError(cause.message);
				}
			})
			.finally(() => {
				if (!cancelled) {
					setLoading(false);
				}
			});

		return () => {
			cancelled = true;
		};
	}, deps);

	return { data, error, loading };
};
