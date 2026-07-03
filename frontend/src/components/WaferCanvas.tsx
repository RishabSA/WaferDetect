export interface Overlay {
  points: [number, number][];
  label: string;
  color: string;
  visible: boolean;
}

export const overlayColors = ["#f87171", "#4ade80", "#60a5fa", "#fbbf24", "#c084fc", "#2dd4bf"];

export const polygonPoints = (points: [number, number][]): string =>
  points.map(([x, y]) => `${x},${y}`).join(" ");

interface WaferCanvasProps {
  imageUrl: string;
  overlays: Overlay[];
  dots?: [number, number][];
  dimImage?: boolean;
  scanning?: boolean;
}

export const WaferCanvas = ({
  imageUrl,
  overlays,
  dots,
  dimImage = false,
  scanning = false,
}: WaferCanvasProps) => {
  return (
    <div className="relative w-full overflow-hidden rounded-full bg-neutral-900 ring-1 ring-cyan-400/25 shadow-[0_0_70px_rgba(34,211,238,0.14)]">
      <img
        src={imageUrl}
        alt="wafer map"
        className={`aspect-square w-full transition-opacity duration-300 ${dimImage ? "opacity-20" : "opacity-100"}`}
      />
      <svg
        viewBox="0 0 1 1"
        preserveAspectRatio="none"
        className="absolute inset-0 h-full w-full"
      >
        {overlays
          .filter((overlay) => overlay.visible)
          .map((overlay, index) => (
            <polygon
              key={`${overlay.label}-${index}`}
              points={polygonPoints(overlay.points)}
              fill={overlay.color}
              fillOpacity={0.14}
              stroke={overlay.color}
              strokeWidth={0.005}
            />
          ))}
        {dots?.map(([x, y], index) => (
          <circle key={index} cx={x} cy={y} r={0.0038} fill="#22d3ee" fillOpacity={0.9} />
        ))}
      </svg>
      {scanning && (
        <div className="absolute inset-x-[6%] h-0.5 animate-scan rounded-full bg-cyan-400/90 shadow-[0_0_14px_3px_rgba(34,211,238,0.75)]" />
      )}
    </div>
  );
};

export default WaferCanvas;
