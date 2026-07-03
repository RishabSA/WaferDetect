import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { api, useApi } from "../api";
import DiagnosisCard from "../components/DiagnosisCard";
import { dollars, percent } from "../format";

const Reports = () => {
  const { stem = "" } = useParams();
  const navigate = useNavigate();
  const [stemInput, setStemInput] = useState(stem || "0101_scratch");

  const { data, error, loading } = useApi(
    () => (stem ? api.diagnose(stem) : Promise.resolve(null)),
    [stem],
  );
  const summary = data?.wafer_summary;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 print:hidden">
        <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          Diagnosis Report
        </h2>
        <input
          value={stemInput}
          onChange={(event) => setStemInput(event.target.value)}
          className="rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm text-neutral-900 transition-colors dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
        />
        <button
          onClick={() => navigate(`/reports/${stemInput}`)}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400"
        >
          Diagnose
        </button>
        {data && (
          <button
            onClick={() => window.print()}
            className="cursor-pointer rounded-md border border-neutral-300 px-3 py-1 text-sm text-neutral-800 transition-colors hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
          >
            Print
          </button>
        )}
      </div>

      {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
      {loading && stem && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400">Diagnosing...</p>
      )}

      {summary && (
        <>
          <div className="flex flex-wrap items-baseline gap-4">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {stem}
            </h3>
            <span className="text-2xl font-bold text-red-500 dark:text-red-400">
              {dollars(summary.total_loss_dollars)}
            </span>
            <span className="text-sm text-neutral-500 dark:text-neutral-400">
              attributed loss · yield {percent(summary.yield)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {[
              ["Gross dies", String(summary.gross_dies)],
              ["Failed dies", String(summary.failed_dies)],
              ["Random yield", percent(summary.yield_random)],
              ["D0 / mm2", summary.d0_per_mm2?.toExponential(2) ?? "n/a"],
              ["Cluster alpha", summary.alpha?.toFixed(2) ?? "none"],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900"
              >
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{label}</p>
                <p className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
                  {value}
                </p>
              </div>
            ))}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {data?.detections.map((detection, index) => (
              <DiagnosisCard key={`${detection.class}-${index}`} detection={detection} />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default Reports;
