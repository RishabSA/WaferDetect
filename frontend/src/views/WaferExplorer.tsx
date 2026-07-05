import { useState } from "react";
import { Link } from "react-router";

import { api, useApi, waferCategories, waferImageUrl } from "../api";
import PageHeader from "../components/PageHeader";
import { buttonGhost, errorText, select, subtle } from "../ui";

const splits = ["", "train", "val", "test"];
const pageSize = 24;

const WaferExplorer = () => {
	const [split, setSplit] = useState("");
	const [category, setCategory] = useState("");
	const [page, setPage] = useState(0);

	const { data, error, loading } = useApi(
		() =>
			api.wafers({ split, category, offset: page * pageSize, limit: pageSize }),
		[split, category, page],
	);

	return (
		<div className="flex animate-fade-up flex-col gap-4">
			<PageHeader kicker="Dataset" title="Wafer Explorer">
				<select
					value={split}
					onChange={event => {
						setSplit(event.target.value);
						setPage(0);
					}}
					className={select}>
					{splits.map(value => (
						<option key={value} value={value}>
							{value || "all splits"}
						</option>
					))}
				</select>
				<select
					value={category}
					onChange={event => {
						setCategory(event.target.value);
						setPage(0);
					}}
					className={select}>
					<option value="">all categories</option>
					{waferCategories.map(value => (
						<option key={value} value={value}>
							{value}
						</option>
					))}
				</select>
				{data && (
					<span className={`font-mono text-xs tabular-nums ${subtle}`}>
						{data.total} wafers
					</span>
				)}
			</PageHeader>

			{error && <p className={errorText}>{error}</p>}

			<div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-6">
				{loading &&
					!data &&
					Array.from({ length: pageSize }, (_, index) => (
						<div
							key={index}
							className="rounded-xl border border-neutral-900/10 bg-panel p-3 dark:border-white/8">
							<div className="aspect-square w-full animate-pulse rounded-full bg-neutral-900/5 dark:bg-white/5" />
							<div className="mt-2 h-3 w-3/4 animate-pulse rounded bg-neutral-900/5 dark:bg-white/5" />
							<div className="mt-1.5 h-2.5 w-1/2 animate-pulse rounded bg-neutral-900/5 dark:bg-white/5" />
						</div>
					))}
				{data?.items.map(item => (
					<Link
						key={item.stem}
						to={`/?stem=${encodeURIComponent(item.stem)}`}
						className="group cursor-pointer rounded-xl border border-neutral-900/10 bg-panel p-3 transition-all hover:border-cyan-600/50 hover:shadow-[0_0_24px_rgba(34,211,238,0.12)] dark:border-white/8 dark:hover:border-cyan-400/50">
						<img
							src={waferImageUrl(item.stem)}
							alt={item.stem}
							className="aspect-square w-full rounded-full border border-neutral-900/10 bg-inset transition-transform group-hover:scale-[1.03] dark:border-white/10"
							loading="lazy"
						/>
						<p className="mt-2 truncate font-mono text-[11px] font-medium text-neutral-800 dark:text-neutral-200">
							{item.stem}
						</p>
						<p className="mt-0.5 font-mono text-[10px] text-neutral-500">
							{item.category} · {item.split}
						</p>
					</Link>
				))}
			</div>

			<div className="flex items-center gap-2">
				<button
					disabled={page === 0}
					onClick={() => setPage(page - 1)}
					className={buttonGhost}>
					Prev
				</button>
				<span className="font-mono text-xs text-neutral-500 tabular-nums dark:text-neutral-400">
					page {page + 1}
					{data ? ` / ${Math.max(1, Math.ceil(data.total / pageSize))}` : ""}
				</span>
				<button
					disabled={!data || (page + 1) * pageSize >= data.total}
					onClick={() => setPage(page + 1)}
					className={buttonGhost}>
					Next
				</button>
			</div>
		</div>
	);
};

export default WaferExplorer;
