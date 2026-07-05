import { label } from "../ui";

interface MetricTileProps {
	label: string;
	value: string;
	accent?: string;
}

const MetricTile = ({
	label: text,
	value,
	accent = "text-neutral-900 dark:text-neutral-100",
}: MetricTileProps) => {
	return (
		<div className="rounded-lg border border-neutral-900/10 bg-inset p-3 transition-colors hover:border-neutral-900/20 dark:border-white/8 dark:hover:border-white/15">
			<p className={label}>{text}</p>
			<p
				className={`mt-1 font-mono text-lg font-semibold tabular-nums ${accent}`}>
				{value}
			</p>
		</div>
	);
};

export default MetricTile;
