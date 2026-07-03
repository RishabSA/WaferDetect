import { useState } from "react";
import { Link } from "react-router";

import { api, useApi, waferImageUrl } from "../api";

const splits = ["", "train", "val", "test"];
const categories = [
  "",
  "center",
  "donut",
  "edge_ring",
  "edge_loc",
  "scratch",
  "random",
  "loc",
  "near_full",
  "swirl",
  "radial_spokes",
  "shot_grid",
  "crescent",
  "half_wafer",
  "wedge",
  "comet",
  "edge_scratch_tiny",
  "edge_scratch_small",
  "edge_scratch_medium",
  "edge_scratch_large",
  "lift_pin",
  "bullseye",
  "gradient",
  "slip_lines",
  "double_ring",
  "combo",
];
const pageSize = 24;
const selectClasses =
  "rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm text-neutral-900 transition-colors dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100";

const WaferExplorer = () => {
  const [split, setSplit] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(0);

  const { data, error, loading } = useApi(
    () => api.wafers({ split, category, offset: page * pageSize, limit: pageSize }),
    [split, category, page],
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          Wafer Explorer
        </h2>
        <select
          value={split}
          onChange={(event) => {
            setSplit(event.target.value);
            setPage(0);
          }}
          className={selectClasses}
        >
          {splits.map((value) => (
            <option key={value} value={value}>
              {value || "all splits"}
            </option>
          ))}
        </select>
        <select
          value={category}
          onChange={(event) => {
            setCategory(event.target.value);
            setPage(0);
          }}
          className={selectClasses}
        >
          {categories.map((value) => (
            <option key={value} value={value}>
              {value || "all categories"}
            </option>
          ))}
        </select>
        {data && (
          <span className="text-sm text-neutral-500 dark:text-neutral-400">
            {data.total} wafers
          </span>
        )}
      </div>

      {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
      {loading && <p className="text-sm text-neutral-500 dark:text-neutral-400">Loading...</p>}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-6">
        {data?.items.map((item) => (
          <Link
            key={item.stem}
            to={`/wafers/${item.stem}`}
            className="cursor-pointer rounded-lg border border-neutral-200 bg-white p-2 transition-colors hover:border-blue-600 dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-blue-400"
          >
            <img
              src={waferImageUrl(item.stem)}
              alt={item.stem}
              className="aspect-square w-full rounded"
              loading="lazy"
            />
            <p className="mt-1 truncate text-xs font-medium text-neutral-900 dark:text-neutral-100">
              {item.stem}
            </p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              {item.category} · {item.split}
            </p>
          </Link>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <button
          disabled={page === 0}
          onClick={() => setPage(page - 1)}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700 disabled:cursor-default disabled:bg-neutral-300 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400 dark:disabled:bg-neutral-700 dark:disabled:text-neutral-400"
        >
          Prev
        </button>
        <span className="text-sm text-neutral-700 dark:text-neutral-300">page {page + 1}</span>
        <button
          disabled={!data || (page + 1) * pageSize >= data.total}
          onClick={() => setPage(page + 1)}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700 disabled:cursor-default disabled:bg-neutral-300 dark:bg-blue-500 dark:text-neutral-950 dark:hover:bg-blue-400 dark:disabled:bg-neutral-700 dark:disabled:text-neutral-400"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default WaferExplorer;
