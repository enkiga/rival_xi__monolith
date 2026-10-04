import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import Navbar from "@/components/reusable/navigation/navbar";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import InvitationDialogue from "@/features/invitation/components/invitation-dialogue";
import type { AuthUserResponse } from "@/types/schemas";

const MainLayout = () => {
	const location = useLocation();
	const userQuery = useGetMeEndpointApiV1AuthMeGet<AuthUserResponse, ApiError>({
		query: {
			retry: false,
			select: (response) => {
				const payload = response as unknown as
					| AuthUserResponse
					| { data: AuthUserResponse };
				return "data" in payload ? payload.data : payload;
			},
		},
	});

	if (userQuery.isPending) {
		return (
			<section className="flex min-h-dvh flex-col gap-8 py-5">
				<div className="flex items-center justify-between">
					<Skeleton className="h-10 w-32" />
					<div className="flex gap-2">
						<Skeleton className="size-9 rounded-lg" />
						<Skeleton className="size-9 rounded-full" />
					</div>
				</div>
				<Skeleton className="h-48 w-full" />
			</section>
		);
	}

	if (userQuery.isError) {
		if (userQuery.error.status === 401) {
			return <Navigate to="/sign-in" replace state={{ from: location }} />;
		}

		return (
			<section className="flex min-h-dvh items-center justify-center">
				<p className="text-sm text-destructive" role="alert">
					{userQuery.error.message}
				</p>
			</section>
		);
	}

	if (userQuery.data.onboarding_required || !userQuery.data.fpl_account) {
		return <Navigate to="/onboarding" replace />;
	}

	return (
		<section className="flex min-h-dvh w-screen flex-col">
			<Navbar user={userQuery.data} />
			<section className="mt-6 lg:mt-10">
				<Outlet context={{ user: userQuery.data }} />
			</section>
			<InvitationDialogue />
		</section>
	);
};

export default MainLayout;
