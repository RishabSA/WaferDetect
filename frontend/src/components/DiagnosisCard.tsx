import type { DiagnosisDetection } from "../api";
import { dollars, percent } from "../format";

interface DiagnosisCardProps {
	detection: DiagnosisDetection;
	color?: string;
}

const DiagnosisCard = ({ detection, color }: DiagnosisCardProps) => {
	return (
		<div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur transition-colors hover:border-white/20">
			<div className="flex items-center justify-between gap-3">
				<span className="flex items-center gap-2 font-semibold text-white">
					{color && (
						<span
							className="h-2.5 w-2.5 rounded-full"
							style={{ backgroundColor: color }}
						/>
					)}
					{detection.class}
				</span>
				<span className="text-sm text-neutral-400">
					conf {percent(detection.confidence)}
				</span>
			</div>
			<p className="mt-1 text-lg font-bold text-red-400 tabular-nums">
				{dollars(detection.yield_loss.dollars)}
			</p>
			<p className="text-xs text-neutral-400">
				{detection.yield_loss.excess_failed.toFixed(0)} excess failed dies ·{" "}
				{percent(detection.yield_loss.yield_loss_frac)} yield loss
			</p>
			<p className="mt-2 text-sm text-neutral-200">
				{detection.diagnosis.mechanism}
			</p>
			<p className="mt-1 text-sm text-cyan-300">{detection.diagnosis.action}</p>
			{detection.kinematics && (
				<span className="mt-2 inline-block rounded-full border border-violet-400/30 bg-violet-400/10 px-2.5 py-0.5 text-xs font-medium text-violet-300">
					kinematics: {detection.kinematics.verdict}
				</span>
			)}
		</div>
	);
};

export default DiagnosisCard;
