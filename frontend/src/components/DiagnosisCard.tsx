import type { DiagnosisDetection } from "../api";
import { dollars, percent } from "../format";

interface DiagnosisCardProps {
  detection: DiagnosisDetection;
}

const DiagnosisCard = ({ detection }: DiagnosisCardProps) => {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex items-center justify-between gap-3">
        <span className="font-semibold text-neutral-900 dark:text-neutral-100">
          {detection.class}
        </span>
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          conf {percent(detection.confidence)}
        </span>
      </div>
      <p className="mt-1 text-lg font-bold text-red-500 dark:text-red-400">
        {dollars(detection.yield_loss.dollars)}
      </p>
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        {detection.yield_loss.excess_failed.toFixed(0)} excess failed dies ·{" "}
        {percent(detection.yield_loss.yield_loss_frac)} yield loss
      </p>
      <p className="mt-2 text-sm text-neutral-800 dark:text-neutral-200">
        {detection.diagnosis.mechanism}
      </p>
      <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
        {detection.diagnosis.action}
      </p>
      {detection.kinematics && (
        <span className="mt-2 inline-block rounded bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
          kinematics: {detection.kinematics.verdict}
        </span>
      )}
    </div>
  );
};

export default DiagnosisCard;
