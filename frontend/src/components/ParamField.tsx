import type { ChangeEvent } from "react";

interface ParamFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: number;
}

const ParamField = ({ label, value, onChange, step = 0.01 }: ParamFieldProps) => {
  return (
    <label className="flex flex-col gap-1 text-xs tracking-wide text-neutral-400 uppercase">
      {label}
      <input
        type="number"
        value={value}
        step={step}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(Number(event.target.value))}
        className="w-28 rounded-lg border border-white/10 bg-neutral-900/80 px-2.5 py-1.5 text-sm text-neutral-200 transition-colors hover:border-cyan-400/40 focus:border-cyan-400 focus:outline-none"
      />
    </label>
  );
};

export default ParamField;
