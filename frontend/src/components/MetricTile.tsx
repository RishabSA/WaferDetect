interface MetricTileProps {
  label: string;
  value: string;
  accent?: string;
}

const MetricTile = ({ label, value, accent = "text-white" }: MetricTileProps) => {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur transition-colors hover:border-white/20">
      <p className="text-xs tracking-wide text-neutral-400 uppercase">{label}</p>
      <p className={`text-lg font-bold tabular-nums ${accent}`}>{value}</p>
    </div>
  );
};

export default MetricTile;
