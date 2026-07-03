import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WaferCanvas, polygonPoints } from "./WaferCanvas";

const square: [number, number][] = [
  [0.1, 0.1],
  [0.4, 0.1],
  [0.4, 0.4],
];

describe("WaferCanvas", () => {
  it("builds SVG points strings", () => {
    expect(polygonPoints(square)).toBe("0.1,0.1 0.4,0.1 0.4,0.4");
  });

  it("renders only visible overlays", () => {
    const overlays = [
      { points: square, label: "scratch", color: "#f87171", visible: true },
      { points: square, label: "donut", color: "#34d399", visible: false },
    ];
    const { container } = render(<WaferCanvas imageUrl="/x.jpg" overlays={overlays} />);
    expect(container.querySelectorAll("polygon").length).toBe(1);
  });

  it("renders dot markers when provided", () => {
    const dots: [number, number][] = [
      [0.5, 0.5],
      [0.2, 0.3],
    ];
    const { container } = render(<WaferCanvas imageUrl="/x.jpg" overlays={[]} dots={dots} />);
    expect(container.querySelectorAll("circle").length).toBe(2);
  });
});
