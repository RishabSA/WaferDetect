import { png } from "../format";

interface FieldHeatmapProps {
  title: string;
  image: string;
}

const FieldHeatmap = ({ title, image }: FieldHeatmapProps) => {
  return (
    <figure className="flex flex-col items-center gap-1">
      <img
        src={png(image)}
        alt={title}
        className="aspect-square w-full max-w-xs rounded-md border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900"
      />
      <figcaption className="text-xs text-neutral-500 dark:text-neutral-400">{title}</figcaption>
    </figure>
  );
};

export default FieldHeatmap;
