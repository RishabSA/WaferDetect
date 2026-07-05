import type { ReactNode } from "react";

import { eyebrow, heading } from "../ui";

interface PageHeaderProps {
	kicker: string;
	title: string;
	children?: ReactNode;
}

const PageHeader = ({ kicker, title, children }: PageHeaderProps) => {
	return (
		<div className="flex flex-col gap-1">
			<p className={eyebrow}>{kicker}</p>
			<div className="flex flex-wrap items-center gap-3">
				<h2 className={heading}>{title}</h2>
				{children}
			</div>
		</div>
	);
};

export default PageHeader;
