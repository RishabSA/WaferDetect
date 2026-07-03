import { useState } from "react";

import type { FieldResponse, ShotGridResponse, ThermalResponse } from "../api";
import { api } from "../api";
import FieldHeatmap from "../components/FieldHeatmap";
import ParamField from "../components/ParamField";
import { png } from "../format";

const tabs = ["thermal", "spincoat", "cmp", "shotgrid"] as const;
type Tab = (typeof tabs)[number];

const spincoatModes = ["center", "annular", "tilt", "edge_bead"];
const cmpModes = ["center", "edge_ring", "donut"];
const verdictColors: Record<string, string> = {
  none: "bg-green-500 dark:bg-green-400",
  stage_or_dose: "bg-yellow-500 dark:bg-yellow-400",
  reticle_defect: "bg-red-500 dark:bg-red-400",
};
const selectClasses =
  "rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm text-neutral-900 transition-colors dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100";

const PhysicsLab = () => {
  const [tab, setTab] = useState<Tab>("thermal");
  const [seed, setSeed] = useState(42);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [steps, setSteps] = useState(250);
  const [ramp, setRamp] = useState(2.0);
  const [edgeLoss, setEdgeLoss] = useState(0.08);
  const [pinStrength, setPinStrength] = useState(0.05);
  const [spotStrength, setSpotStrength] = useState(0);
  const [filmMode, setFilmMode] = useState("center");
  const [cmpMode, setCmpMode] = useState("edge_ring");
  const [shotMode, setShotMode] = useState("intra");
  const [thermal, setThermal] = useState<ThermalResponse | null>(null);
  const [film, setFilm] = useState<FieldResponse | null>(null);
  const [shot, setShot] = useState<ShotGridResponse | null>(null);

  const run = async () => {
    setRunning(true);
    setError("");
    try {
      if (tab === "thermal") {
        setThermal(
          await api.thermal({
            steps,
            ramp_per_step: ramp,
            edge_loss: edgeLoss,
            pin_strength: pinStrength,
            spot_x: spotStrength > 0 ? 0 : null,
            spot_y: spotStrength > 0 ? 0 : null,
            spot_strength: spotStrength,
            seed,
          }),
        );
      } else if (tab === "spincoat") {
        setFilm(await api.spincoat({ mode: filmMode, seed }));
      } else if (tab === "cmp") {
        setFilm(await api.cmp({ mode: cmpMode, seed }));
      } else {
        setShot(await api.shotgrid({ mode: shotMode, seed }));
      }
    } catch (cause) {
      setError((cause as Error).message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">Physics Lab</h2>

      <div className="flex flex-wrap gap-1">
        {tabs.map((name) => (
          <button
            key={name}
            onClick={() => setTab(name)}
            className={`cursor-pointer rounded-md px-3 py-1 text-sm transition-colors hover:bg-neutral-200 dark:hover:bg-neutral-800 ${
              tab === name
                ? "bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400"
                : "bg-white text-neutral-800 dark:bg-neutral-900 dark:text-neutral-200"
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        {tab === "thermal" && (
          <>
            <ParamField label="steps" value={steps} onChange={setSteps} step={50} />
            <ParamField label="ramp K/step" value={ramp} onChange={setRamp} step={0.5} />
            <ParamField label="edge loss" value={edgeLoss} onChange={setEdgeLoss} />
            <ParamField label="pin strength" value={pinStrength} onChange={setPinStrength} />
            <ParamField label="cold spot" value={spotStrength} onChange={setSpotStrength} />
          </>
        )}
        {tab === "spincoat" && (
          <select value={filmMode} onChange={(event) => setFilmMode(event.target.value)} className={selectClasses}>
            {spincoatModes.map((mode) => (
              <option key={mode}>{mode}</option>
            ))}
          </select>
        )}
        {tab === "cmp" && (
          <select value={cmpMode} onChange={(event) => setCmpMode(event.target.value)} className={selectClasses}>
            {cmpModes.map((mode) => (
              <option key={mode}>{mode}</option>
            ))}
          </select>
        )}
        {tab === "shotgrid" && (
          <select value={shotMode} onChange={(event) => setShotMode(event.target.value)} className={selectClasses}>
            <option value="intra">intra reticle</option>
            <option value="inter">inter field</option>
          </select>
        )}
        <ParamField label="seed" value={seed} onChange={setSeed} step={1} />
        <button
          onClick={run}
          disabled={running}
          className="cursor-pointer rounded-md bg-blue-600 px-4 py-1.5 text-sm text-white transition-colors hover:bg-blue-700 disabled:cursor-default disabled:bg-neutral-300 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400 dark:disabled:bg-neutral-700 dark:disabled:text-neutral-400"
        >
          {running ? "Simulating..." : "Run simulation"}
        </button>
        {error && <span className="text-sm text-red-500 dark:text-red-400">{error}</span>}
      </div>

      {tab === "thermal" && thermal && (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            {thermal.stats.min_temperature.toFixed(0)} K to{" "}
            {thermal.stats.max_temperature.toFixed(0)} K
          </p>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <FieldHeatmap title="temperature" image={thermal.temperature} />
            <FieldHeatmap title="thermal stress" image={thermal.stress} />
            <FieldHeatmap title="slip probability" image={thermal.slip_probability} />
            <FieldHeatmap title="generated slip wafer" image={thermal.sample} />
          </div>
        </div>
      )}
      {(tab === "spincoat" || tab === "cmp") && film && (
        <div className="grid grid-cols-2 gap-4 md:max-w-xl">
          <FieldHeatmap title="failure probability" image={film.probability} />
          <FieldHeatmap title="generated wafer" image={film.sample} />
        </div>
      )}
      {tab === "shotgrid" && shot && (
        <div className="flex flex-col gap-2">
          <span
            className={`w-fit rounded px-2 py-0.5 text-xs font-semibold text-white dark:text-neutral-950 ${
              verdictColors[shot.verdict.verdict] ?? "bg-neutral-500 dark:bg-neutral-400"
            }`}
          >
            analysis verdict: {shot.verdict.verdict}
          </span>
          <div className="grid grid-cols-2 gap-4 md:max-w-xl">
            <FieldHeatmap title="shot-grid field" image={shot.field} />
            <img
              src={png(shot.sample)}
              alt="generated wafer"
              className="aspect-square w-full max-w-xs rounded-md border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default PhysicsLab;
