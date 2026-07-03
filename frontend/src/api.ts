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

export interface Detection {
  class: string;
  confidence: number;
  polygon: [number, number][];
  area_frac: number;
  centroid_r: number;
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

export interface DiagnosisReport {
  detections: DiagnosisDetection[];
  wafer_summary: WaferSummary;
}

export interface YieldPanel {
  summary: WaferSummary;
  radial: number[];
  zones: { center: number; mid: number; edge: number };
  regions: YieldLoss[];
}

export interface ParetoResponse {
  wafers: number;
  pareto: [string, number][];
}

export interface GenerateResponse {
  categories: string[];
  labels: string[];
  image: string;
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

const postJson = <T>(path: string, body: unknown): Promise<T> =>
  request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const api = {
  wafers: (params: { split?: string; category?: string; offset?: number; limit?: number }) => {
    const entries = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== "")
      .map(([key, value]) => [key, String(value)]);
    const query = new URLSearchParams(entries);
    return request<WaferList>(`/api/wafers?${query}`);
  },
  waferDetail: (stem: string) => request<WaferDetail>(`/api/wafers/${stem}`),
  detect: (stem: string) =>
    request<{ detections: Detection[] }>(`/api/detect?stem=${stem}`, { method: "POST" }),
  diagnose: (stem: string) => request<DiagnosisReport>(`/api/diagnose/${stem}`),
  yieldWafer: (stem: string) => request<YieldPanel>(`/api/yield/wafer/${stem}`),
  pareto: (split: string, limit: number) =>
    request<ParetoResponse>(`/api/yield/pareto?split=${split}&limit=${limit}`),
  generate: (body: {
    categories: string[] | null;
    physics_frac: number;
    die_grid: number;
    seed: number;
  }) => postJson<GenerateResponse>("/api/generate", body),
  thermal: (body: Record<string, number | null>) =>
    postJson<ThermalResponse>("/api/physics/thermal", body),
  spincoat: (body: { mode: string; seed: number }) =>
    postJson<FieldResponse>("/api/physics/spincoat", body),
  cmp: (body: { mode: string; seed: number }) =>
    postJson<FieldResponse>("/api/physics/cmp", body),
  shotgrid: (body: { mode: string; seed: number }) =>
    postJson<ShotGridResponse>("/api/physics/shotgrid", body),
};

export const waferImageUrl = (stem: string): string => `/api/wafers/${stem}/image`;

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
      .then((result) => {
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
