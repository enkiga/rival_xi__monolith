import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import {
	useGetLeagueEndpointApiV1LeaguesSlugGet,
	useGetMemberGameweekEndpointApiV1LeaguesSlugGameweeksGameweekMembersMemberIdGet,
} from "@/api/leagues/leagues";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import type {
	LeagueDetailResponse,
	MemberGameweekResponse,
} from "@/types/schemas";
import TeamFieldView from "../components/team-field-view";
import TeamSummary from "../components/team-summary";

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const GameweekMemberScreen = () => {
	const { slug, gameweek, memberId } = useParams<{
		slug: string;
		gameweek: string;
		memberId: string;
	}>();
	const gameweekNumber = Number(gameweek);
	const memberIdNumber = Number(memberId);
	const hasValidParams =
		Boolean(slug) &&
		Number.isInteger(gameweekNumber) &&
		Number.isInteger(memberIdNumber);
	const leagueQuery = useGetLeagueEndpointApiV1LeaguesSlugGet<
		LeagueDetailResponse,
		ApiError
	>(slug ?? "", {
		query: {
			enabled: hasValidParams,
			select: (response) =>
				unwrapResponse(response as unknown as LeagueDetailResponse),
		},
	});
	const memberQuery =
		useGetMemberGameweekEndpointApiV1LeaguesSlugGameweeksGameweekMembersMemberIdGet<
			MemberGameweekResponse,
			ApiError
		>(slug ?? "", gameweekNumber, memberIdNumber, {
			query: {
				enabled: hasValidParams,
				select: (response) =>
					unwrapResponse(response as unknown as MemberGameweekResponse),
			},
		});

	if (!hasValidParams || !slug) {
		return (
			<p className="text-sm text-destructive" role="alert">
				The squad URL is invalid.
			</p>
		);
	}

	if (leagueQuery.isPending || memberQuery.isPending) {
		return (
			<section className="flex flex-col gap-6 py-8">
				<header className="flex items-center gap-4 border-b border-muted-foreground pb-4">
					<Skeleton className="size-9" />
					<div className="space-y-2">
						<Skeleton className="h-7 w-48" />
						<Skeleton className="h-4 w-32" />
					</div>
				</header>
				<TeamSummary isLoading />
				<TeamFieldView isLoading />
			</section>
		);
	}

	if (leagueQuery.isError || memberQuery.isError) {
		return (
			<p className="text-sm text-destructive" role="alert">
				{leagueQuery.error?.message ?? memberQuery.error?.message}
			</p>
		);
	}

	const member = leagueQuery.data.members.find(
		(item) => item.id === memberIdNumber,
	);

	return (
		<section className="flex flex-col gap-6 py-8">
			<header className="flex items-center gap-4 border-b border-muted-foreground pb-4">
				<Button
					size="icon-lg"
					variant="outline"
					render={<Link to={`/league/${slug}/gameweek/${gameweekNumber}`} />}
				>
					<ArrowLeft />
					<span className="sr-only">Back to league</span>
				</Button>
				<div className="min-w-0">
					<h1 className="text-base font-semibold lg:text-2xl lg:font-bold">
						{leagueQuery.data.name}
					</h1>
					<div className="flex flex-wrap items-center gap-2">
						<p className="text-sm text-muted-foreground">
							{member?.team_name ?? `Entry ${memberQuery.data.fpl_entry_id}`}
							<span className="px-1.5" aria-hidden="true">
								·
							</span>
							GWK{memberQuery.data.gameweek}
						</p>
					</div>
				</div>
			</header>

			<TeamSummary data={memberQuery.data} />
			<TeamFieldView picks={memberQuery.data.picks} />
		</section>
	);
};

export default GameweekMemberScreen;
