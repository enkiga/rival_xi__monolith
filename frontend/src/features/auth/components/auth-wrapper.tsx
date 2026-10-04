import type { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import AuthContentPanel from "./auth-content-panel";

type Props = {
	children: ReactNode;
	className?: string;
	panelContent?: ReactNode;
};

const AuthWrapper = ({ children, className, panelContent }: Props) => {
	return (
		<section className="bg-[linear-gradient(to_bottom,--theme(--color-background/35%),--theme(--color-background/35%)),url('@/assets/auth-bg.png')] bg-cover bg-center flex min-h-svh items-center justify-center bg-muted p-6 md:p-10">
			<div className="w-full max-w-sm md:max-w-4xl">
				<Card className="overflow-hidden p-0 border border-primary">
					<CardContent className="grid p-0 md:grid-cols-2">
						<AuthContentPanel>{panelContent}</AuthContentPanel>
						<div className={cn("p-6 md:p-8", className)}>{children}</div>
					</CardContent>
				</Card>
			</div>
		</section>
	);
};

export default AuthWrapper;
