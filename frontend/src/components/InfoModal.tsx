import type { ReactNode } from "react";
import { FaTimes } from "react-icons/fa";

interface InfoModalProps {
	title: string;
	onClose: () => void;
	children: ReactNode;
}

const InfoModal = ({ title, onClose, children }: InfoModalProps) => {
	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center p-4">
			<div className="absolute inset-0 bg-black/60" onClick={onClose} />
			<div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-neutral-950 p-5 shadow-xl">
				<div className="mb-3 flex items-center justify-between">
					<h3 className="text-sm font-semibold text-white">{title}</h3>
					<button
						onClick={onClose}
						aria-label="Close"
						className="cursor-pointer rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-white/5 hover:text-white">
						<FaTimes size={12} />
					</button>
				</div>
				<div className="flex flex-col gap-2 text-sm text-neutral-300">
					{children}
				</div>
			</div>
		</div>
	);
};

export default InfoModal;
