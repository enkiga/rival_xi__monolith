import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = {
	children: ReactNode;
	className?: string;
};

const SectionWrapper = (props: Props) => {
	return (
		<section className={cn("container mx-auto px-4", props.className)}>
			{props.children}
		</section>
	);
};

export default SectionWrapper;
