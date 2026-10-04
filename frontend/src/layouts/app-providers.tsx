import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { Toaster } from "@/components/ui/toast";
import { queryClient } from "@/lib/query-client";

type Props = {
	children: ReactNode;
};

const AppProviders = ({ children }: Props) => {
	return (
		<QueryClientProvider client={queryClient}>
			<Toaster>{children}</Toaster>
		</QueryClientProvider>
	);
};

export default AppProviders;
