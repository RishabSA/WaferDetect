import { png } from "../format";
import { label } from "../ui";

interface FieldHeatmapProps {
	title: string;
	image: string;
}

const FieldHeatmap = ({ title, image }: FieldHeatmapProps) => {
	return (
		<figure className="flex flex-col items-center gap-1.5">
			<img
				src={png(image)}
				alt={title}
				className="aspect-square w-full max-w-xs rounded-lg border border-neutral-900/10 bg-inset dark:border-white/10"
			/>
			<figcaption className={label}>{title}</figcaption>
		</figure>
	);
};

export default FieldHeatmap;
