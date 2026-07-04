import { useEffect, useRef, useState } from "react";

const durationMs = 900;

export const useCountUp = (target: number): number => {
	const [value, setValue] = useState(0);
	const fromRef = useRef<number>(0);

	useEffect(() => {
		const from = fromRef.current;
		const start = performance.now();
		let frame = 0;

		const tick = (now: number) => {
			const progress = Math.min((now - start) / durationMs, 1);
			const eased = 1 - (1 - progress) ** 3;
			const current = from + (target - from) * eased;
			setValue(current);
			fromRef.current = current;
			if (progress < 1) {
				frame = requestAnimationFrame(tick);
			}
		};

		frame = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(frame);
	}, [target]);

	return value;
};

export default useCountUp;
