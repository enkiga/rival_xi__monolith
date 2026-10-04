import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = {
	children?: ReactNode;
	className?: string;
};

const AuthContentPanel = ({ children, className }: Props) => (
	<div className={cn("relative hidden min-h-144 md:block border-r ", className)}>
		{children}
	</div>
);

export default AuthContentPanel;
