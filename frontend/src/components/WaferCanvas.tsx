export interface Overlay {
  points: [number, number][];
  label: string;
  color: string;
  visible: boolean;
}

export const overlayColors = ["#ef4444", "#22c55e", "#3b82f6", "#f59e0b", "#a855f7", "#14b8a6"];

export const polygonPoints = (points: [number, number][]): string =>
  points.map(([x, y]) => `${x},${y}`).join(" ");

interface WaferCanvasProps {
  imageUrl: string;
  overlays: Overlay[];
}

export const WaferCanvas = ({ imageUrl, overlays }: WaferCanvasProps) => {
  return (
    <div className="relative w-full max-w-xl overflow-hidden rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
      <img src={imageUrl} alt="wafer map" className="aspect-square w-full" />
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
              fillOpacity={0.12}
              stroke={overlay.color}
              strokeWidth={0.005}
            />
          ))}
      </svg>
    </div>
  );
};

export default WaferCanvas;
