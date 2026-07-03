import { png } from "../format";

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
        className="aspect-square w-full max-w-xs rounded-xl border border-white/10 bg-white/5"
      />
      <figcaption className="text-xs tracking-wide text-neutral-400 uppercase">{title}</figcaption>
    </figure>
  );
};

export default FieldHeatmap;
