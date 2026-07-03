import type { ChangeEvent } from "react";

interface ParamFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: number;
}

const ParamField = ({ label, value, onChange, step = 0.01 }: ParamFieldProps) => {
  return (
    <label className="flex flex-col gap-1 text-xs text-neutral-600 dark:text-neutral-400">
      {label}
      <input
        type="number"
        value={value}
        step={step}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(Number(event.target.value))}
        className="w-28 rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm text-neutral-900 transition-colors focus:border-blue-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 dark:focus:border-blue-400"
      />
    </label>
  );
};

export default ParamField;
