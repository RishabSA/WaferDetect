import { useEffect, useState } from "react";

const defaultDelayMs = 500;

export const useDebounced = <T>(
	value: T,
	delayMs: number = defaultDelayMs,
): T => {
	const [debounced, setDebounced] = useState(value);

	useEffect(() => {
		const timer = setTimeout(() => setDebounced(value), delayMs);
		return () => clearTimeout(timer);
	}, [value, delayMs]);

	return debounced;
};

export default useDebounced;
