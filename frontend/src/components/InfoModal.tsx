import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { FaTimes } from "react-icons/fa";

import { cardTitle } from "../ui";

interface InfoModalProps {
	title: string;
	onClose: () => void;
	children: ReactNode;
}

const InfoModal = ({ title, onClose, children }: InfoModalProps) => {
	// Portal to body: transformed ancestors (e.g. animate-fade-up) would otherwise
	// re-anchor position:fixed to themselves instead of the viewport
	return createPortal(
		<div className="fixed inset-0 z-50 flex items-center justify-center p-4">
			<div
				className="absolute inset-0 bg-black/40 dark:bg-black/60"
				onClick={onClose}
			/>
			<div className="relative max-h-[85vh] w-full max-w-md overflow-y-auto rounded-xl border border-neutral-900/10 bg-panel p-5 shadow-[0_24px_60px_rgba(0,0,0,0.25)] dark:border-white/10 dark:shadow-[0_24px_60px_rgba(0,0,0,0.6)]">
				<div className="mb-3 flex items-center justify-between">
					<h3 className={cardTitle}>{title}</h3>
					<button
						onClick={onClose}
						aria-label="Close"
						className="cursor-pointer rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-neutral-900/5 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-white/5 dark:hover:text-white">
						<FaTimes size={12} />
					</button>
				</div>
				<div className="flex flex-col gap-2 text-sm leading-relaxed text-neutral-600 dark:text-neutral-300">
					{children}
				</div>
			</div>
		</div>,
		document.body,
	);
};

export default InfoModal;
