import { Activity, GalleryVerticalEnd, SquircleDashed } from "lucide-react";
import type { ReactNode } from "react";
import { useGetLeaguesEndpointApiV1LeaguesGet } from "@/api/leagues/leagues";
import authBg from "@/assets/auth-bg.png";
import SectionWrapper from "@/components/reusable/section-wrapper";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import type { LeagueListResponse } from "@/types/schemas";
import LeagueDialog from "./league-dialog";

const HomeIntroSection = () => {
	const leaguesQuery = useGetLeaguesEndpointApiV1LeaguesGet<
		LeagueListResponse,
		ApiError
	>(
		{ page: 1, page_size: 10 },
		{
			query: {
				select: (response) => {
					const payload = response as unknown as
						| LeagueListResponse
						| { data: LeagueListResponse };
					return "data" in payload ? payload.data : payload;
				},
			},
		},
	);

	const unavailableCount = leaguesQuery.isError ? "—" : 0;

	return (
		<div className="relative flex min-h-80 flex-col gap-4 overflow-hidden">
			<img
				src={authBg}
				alt=""
				className="absolute inset-0 size-full object-cover object-center"
				aria-hidden="true"
			/>
			<div
				className="pointer-events-none absolute inset-0"
				style={{
					backgroundImage:
						"linear-gradient(to bottom, transparent 0%, color-mix(in oklch, var(--color-background) 55%, transparent) 55%, var(--color-background) 100%)",
				}}
			/>
			<SectionWrapper className="relative z-10 lg:py-20 py-10">
				<div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
					<div className="flex flex-col gap-1.5">
						<h2 className="text-3xl font-semibold">Your Rival XI Leagues</h2>
						<p className="text-sm text-muted-foreground">
							Manage and track all your Rival XI leagues in one place.
						</p>
					</div>
					<LeagueDialog />
				</div>
				<div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
					<HomeStatCards
						icon={<GalleryVerticalEnd />}
						count={leaguesQuery.data?.total ?? unavailableCount}
						label="All leagues"
						isLoading={leaguesQuery.isPending}
					/>
					<HomeStatCards
						icon={<Activity />}
						count={leaguesQuery.data?.active_count ?? unavailableCount}
						label="Active leagues"
						isLoading={leaguesQuery.isPending}
					/>
					<HomeStatCards
						icon={<SquircleDashed />}
						count={leaguesQuery.data?.draft_count ?? unavailableCount}
						label="Draft leagues"
						isLoading={leaguesQuery.isPending}
					/>
				</div>
			</SectionWrapper>
		</div>
	);
};

export default HomeIntroSection;

const HomeStatCards = ({
	icon,
	count,
	label,
	isLoading,
}: {
	icon: ReactNode;
	count: ReactNode;
	label: string;
	isLoading: boolean;
}) => {
	return (
		<Card className="flex flex-row items-center gap-4 p-4">
			<div className="rounded-sm bg-primary/60 p-4 text-fpl-pink">{icon}</div>
			<div className="flex flex-col gap-1">
				{isLoading ? (
					<Skeleton className="h-8 w-12" />
				) : (
					<p className="text-2xl font-bold">{count}</p>
				)}
				<p className="text-sm text-muted-foreground">{label}</p>
			</div>
		</Card>
	);
};
