import type { DiagnosisDetection } from "../api";
import { dollars, percent } from "../format";

interface DiagnosisCardProps {
	detection: DiagnosisDetection;
	color?: string;
}

const DiagnosisCard = ({ detection, color }: DiagnosisCardProps) => {
	return (
		<div className="rounded-lg border border-neutral-900/10 bg-neutral-900/3 p-4 transition-colors hover:border-neutral-900/20 dark:border-white/8 dark:bg-white/3 dark:hover:border-white/15">
			<div className="flex items-center justify-between gap-3">
				<span className="flex items-center gap-2 font-semibold text-neutral-900 dark:text-white">
					{color && (
						<span
							className="h-2.5 w-2.5 rounded-full"
							style={{ backgroundColor: color }}
						/>
					)}
					{detection.class}
				</span>
				<span className="font-mono text-xs text-neutral-500 tabular-nums dark:text-neutral-400">
					conf {percent(detection.confidence)}
				</span>
			</div>
			<p className="mt-1 font-mono text-lg font-bold text-red-600 tabular-nums dark:text-red-400">
				{dollars(detection.yield_loss.dollars)}
			</p>
			<p className="font-mono text-[11px] text-neutral-500 tabular-nums dark:text-neutral-400">
				{detection.yield_loss.excess_failed.toFixed(0)} excess failed dies ·{" "}
				{percent(detection.yield_loss.yield_loss_frac)} yield loss
			</p>
			<p className="mt-2 text-sm text-neutral-700 dark:text-neutral-200">
				{detection.diagnosis.mechanism}
			</p>
			<p className="mt-1 text-sm text-cyan-700 dark:text-cyan-300">
				{detection.diagnosis.action}
			</p>
			{detection.kinematics && (
				<span className="mt-2 inline-block rounded-md border border-violet-600/30 bg-violet-500/10 px-2 py-0.5 font-mono text-[11px] font-medium text-violet-700 dark:border-violet-400/30 dark:bg-violet-400/10 dark:text-violet-300">
					kinematics: {detection.kinematics.verdict}
				</span>
			)}
		</div>
	);
};

export default DiagnosisCard;
