import { useState } from "react";
import { Link, useParams } from "react-router";

import type { Detection } from "../api";
import { api, useApi, waferImageUrl } from "../api";
import { overlayColors, WaferCanvas } from "../components/WaferCanvas";
import { percent } from "../format";

const DetectionViewer = () => {
  const { stem = "" } = useParams();
  const [detections, setDetections] = useState<Detection[]>([]);
  const [hidden, setHidden] = useState<number[]>([]);
  const [detecting, setDetecting] = useState(false);
  const [detectError, setDetectError] = useState("");

  const { data: detail, error, loading } = useApi(() => api.waferDetail(stem), [stem]);

  const runDetection = async () => {
    setDetecting(true);
    setDetectError("");
    try {
      const result = await api.detect(stem);
      setDetections(result.detections);
      setHidden([]);
    } catch (cause) {
      setDetectError((cause as Error).message);
    } finally {
      setDetecting(false);
    }
  };

  const toggleHidden = (index: number) =>
    setHidden(
      hidden.includes(index) ? hidden.filter((item) => item !== index) : [...hidden, index],
    );

  const overlays = detections.map((detection, index) => ({
    points: detection.polygon,
    label: detection.class,
    color: overlayColors[index % overlayColors.length],
    visible: !hidden.includes(index),
  }));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">{stem}</h2>
        {detail && (
          <span className="text-sm text-neutral-500 dark:text-neutral-400">
            {detail.category} · {detail.split} split
          </span>
        )}
        <button
          onClick={runDetection}
          disabled={detecting}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700 disabled:cursor-default disabled:bg-neutral-300 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400 dark:disabled:bg-neutral-700 dark:disabled:text-neutral-400"
        >
          {detecting ? "Detecting..." : "Run detection"}
        </button>
        <Link
          to={`/reports/${stem}`}
          className="cursor-pointer rounded-md border border-blue-600 px-3 py-1 text-sm text-blue-600 transition-colors hover:bg-blue-50 dark:border-blue-400 dark:text-blue-400 dark:hover:bg-blue-950"
        >
          Open report
        </Link>
      </div>

      {(error || detectError) && (
        <p className="text-sm text-red-500 dark:text-red-400">{error || detectError}</p>
      )}
      {loading && <p className="text-sm text-neutral-500 dark:text-neutral-400">Loading...</p>}

      <div className="flex flex-col gap-6 md:flex-row">
        <WaferCanvas imageUrl={waferImageUrl(stem)} overlays={overlays} />

        <div className="flex min-w-64 flex-col gap-2">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400">
            Ground truth
          </h3>
          <div className="flex flex-wrap gap-1">
            {detail?.instances.map((instance, index) => (
              <span
                key={`${instance.class}-${index}`}
                className="rounded bg-neutral-200 px-2 py-0.5 text-xs text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200"
              >
                {instance.class}
              </span>
            ))}
          </div>

          <h3 className="mt-3 text-sm font-semibold text-neutral-500 dark:text-neutral-400">
            Model detections
          </h3>
          {detections.length === 0 && (
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              Run detection to see predictions.
            </p>
          )}
          {detections.map((detection, index) => (
            <button
              key={`${detection.class}-${index}`}
              onClick={() => toggleHidden(index)}
              className={`flex cursor-pointer items-center gap-2 rounded-md border px-2 py-1 text-left text-sm transition-colors hover:border-blue-600 dark:hover:border-blue-400 ${
                hidden.includes(index)
                  ? "border-neutral-200 text-neutral-400 opacity-50 dark:border-neutral-800 dark:text-neutral-600"
                  : "border-neutral-300 text-neutral-800 dark:border-neutral-700 dark:text-neutral-200"
              }`}
            >
              <span
                className="h-3 w-3 rounded-sm"
                style={{ backgroundColor: overlayColors[index % overlayColors.length] }}
              />
              {detection.class}
              <span className="ml-auto text-xs text-neutral-500 dark:text-neutral-400">
                {percent(detection.confidence)}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DetectionViewer;
