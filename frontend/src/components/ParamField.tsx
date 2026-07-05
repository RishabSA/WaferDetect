import type { ChangeEvent } from "react";

import { input, label } from "../ui";

interface ParamFieldProps {
	label: string;
	value: number;
	onChange: (value: number) => void;
	step?: number;
}

const ParamField = ({
	label: text,
	value,
	onChange,
	step = 0.01,
}: ParamFieldProps) => {
	return (
		<label className={`flex flex-col gap-1.5 ${label}`}>
			{text}
			<input
				type="number"
				value={value}
				step={step}
				onChange={(event: ChangeEvent<HTMLInputElement>) =>
					onChange(Number(event.target.value))
				}
				className={`w-28 font-mono tabular-nums ${input}`}
			/>
		</label>
	);
};

export default ParamField;
