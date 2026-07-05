import type { IconType } from "react-icons";
import { FaDesktop, FaMoon, FaSun } from "react-icons/fa";

import type { ThemePreference } from "../theme";
import { setThemePreference, useThemePreference } from "../theme";
import { segmented } from "../ui";

const options: { value: ThemePreference; label: string; icon: IconType }[] = [
	{ value: "light", label: "Light theme", icon: FaSun },
	{ value: "dark", label: "Dark theme", icon: FaMoon },
	{ value: "system", label: "Follow system theme", icon: FaDesktop },
];

const ThemeToggle = () => {
	const preference = useThemePreference();

	return (
		<div className={`${segmented} w-full`}>
			{options.map(({ value, label: text, icon: Icon }) => (
				<button
					key={value}
					onClick={() => setThemePreference(value)}
					aria-label={text}
					title={text}
					aria-pressed={preference === value}
					className={`flex flex-1 cursor-pointer items-center justify-center rounded-md py-1.5 transition-colors ${
						preference === value
							? "bg-cyan-500/10 text-cyan-700 dark:bg-cyan-400/15 dark:text-cyan-300"
							: "text-neutral-500 hover:bg-neutral-900/5 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-white/5 dark:hover:text-neutral-200"
					}`}>
					<Icon size={12} />
				</button>
			))}
		</div>
	);
};

export default ThemeToggle;
