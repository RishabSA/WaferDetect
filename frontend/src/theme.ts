import { useSyncExternalStore } from "react";

export type ThemePreference = "light" | "dark" | "system";

const storageKey = "waferdetect-theme";
const themeColors = { dark: "#070b12", light: "#eef1f6" } as const;

const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
const listeners = new Set<() => void>();

const stored = localStorage.getItem(storageKey);
let preference: ThemePreference =
	stored === "light" || stored === "system" ? stored : "dark";

const isDark = (): boolean =>
	preference === "system" ? systemDark.matches : preference === "dark";

const apply = () => {
	const dark = isDark();
	document.documentElement.classList.toggle("dark", dark);
	document
		.querySelector('meta[name="theme-color"]')
		?.setAttribute("content", dark ? themeColors.dark : themeColors.light);
};

const notify = () => {
	apply();
	listeners.forEach(listener => listener());
};

systemDark.addEventListener("change", () => {
	if (preference === "system") {
		notify();
	}
});

export const setThemePreference = (next: ThemePreference) => {
	preference = next;
	localStorage.setItem(storageKey, next);
	notify();
};

const subscribe = (listener: () => void) => {
	listeners.add(listener);
	return () => {
		listeners.delete(listener);
	};
};

export const useThemePreference = (): ThemePreference =>
	useSyncExternalStore(subscribe, () => preference);

export const useIsDark = (): boolean => useSyncExternalStore(subscribe, isDark);

// the pre-paint script in index.html only sets the class; sync the meta too
apply();
