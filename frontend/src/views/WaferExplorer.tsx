import { useState } from "react";
import { Link } from "react-router";

import { api, useApi, waferCategories, waferImageUrl } from "../api";
import { buttonGhost, errorText, heading, select, subtle } from "../ui";

const splits = ["", "train", "val", "test"];
const pageSize = 24;

const WaferExplorer = () => {
  const [split, setSplit] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(0);

  const { data, error, loading } = useApi(
    () => api.wafers({ split, category, offset: page * pageSize, limit: pageSize }),
    [split, category, page],
  );

  return (
    <div className="flex animate-fade-up flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className={heading}>Wafer Explorer</h2>
        <select
          value={split}
          onChange={(event) => {
            setSplit(event.target.value);
            setPage(0);
          }}
          className={select}
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
          className={select}
        >
          <option value="">all categories</option>
          {waferCategories.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        {data && <span className={subtle}>{data.total} wafers</span>}
      </div>

      {error && <p className={errorText}>{error}</p>}
      {loading && <p className={subtle}>Loading...</p>}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-6">
        {data?.items.map((item) => (
          <Link
            key={item.stem}
            to={`/?stem=${encodeURIComponent(item.stem)}`}
            className="group cursor-pointer rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur transition-all hover:border-cyan-400/50 hover:bg-white/10 hover:shadow-[0_0_24px_rgba(34,211,238,0.15)]"
          >
            <img
              src={waferImageUrl(item.stem)}
              alt={item.stem}
              className="aspect-square w-full rounded-full border border-white/10 transition-transform group-hover:scale-[1.03]"
              loading="lazy"
            />
            <p className="mt-2 truncate text-xs font-medium text-neutral-100">{item.stem}</p>
            <p className="text-xs text-neutral-400">
              {item.category} · {item.split}
            </p>
          </Link>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <button disabled={page === 0} onClick={() => setPage(page - 1)} className={buttonGhost}>
          Prev
        </button>
        <span className="text-sm text-neutral-300 tabular-nums">page {page + 1}</span>
        <button
          disabled={!data || (page + 1) * pageSize >= data.total}
          onClick={() => setPage(page + 1)}
          className={buttonGhost}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default WaferExplorer;
