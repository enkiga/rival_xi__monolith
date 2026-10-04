import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import {
	useGetLeagueEndpointApiV1LeaguesSlugGet,
	useGetMemberGameweekEndpointApiV1LeaguesSlugGameweeksGameweekMembersMemberIdGet,
} from "@/api/leagues/leagues";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import type {
	LeagueDetailResponse,
	MemberGameweekResponse,
} from "@/types/schemas";
import BenchCard from "../components/bench-card";
import TeamFieldView from "../components/team-field-view";
import TeamSummary from "../components/team-summary";
import SectionWrapper from "@/components/reusable/section-wrapper";

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
				<Skeleton className="h-10 w-24" />
				<div className="grid gap-6 lg:grid-cols-3">
					<div className="flex flex-col gap-6 lg:col-span-2">
						<header className="flex items-center gap-4">
							<Skeleton className="size-14 rounded-full" />
							<Skeleton className="h-7 w-48" />
						</header>
						<TeamSummary isLoading />
						<TeamFieldView isLoading />
					</div>
					<Skeleton className="min-h-80" />
				</div>
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

	if (!member) {
		return (
			<p className="text-sm text-destructive" role="alert">
				The league member could not be found.
			</p>
		);
	}

	const initials = member.manager_name
		.split(" ")
		.filter(Boolean)
		.slice(0, 2)
		.map((word) => word[0])
		.join("")
		.toUpperCase();

	return (
		<SectionWrapper className="flex flex-col gap-6 py-8">
			<Link to={`/league/${slug}/gameweek/${gameweekNumber}`}>
				<Button
					size="lg"
					variant="outline"
					className="mt-2 flex cursor-pointer items-center gap-2"
				>
					<ArrowLeft />
					Back
				</Button>
			</Link>

			<div className="grid gap-6 lg:grid-cols-3 lg:items-start">
				<div className="flex min-w-0 flex-col gap-6 lg:col-span-2">
					<header className="flex items-center gap-4">
						<Avatar className="size-14 shrink-0 border-0 after:border-0 sm:size-16">
							<AvatarFallback className="bg-primary/60 text-lg font-semibold">
								{initials}
							</AvatarFallback>
						</Avatar>
						<h1 className="truncate text-xl font-semibold sm:text-2xl">
							{member.manager_name}
						</h1>
					</header>

					<TeamSummary data={memberQuery.data} />
					<TeamFieldView picks={memberQuery.data.picks} />
				</div>

				<aside className="lg:pt-55">
					<BenchCard
						picks={memberQuery.data.picks}
						points={memberQuery.data.points_on_bench}
					/>
				</aside>
			</div>
		</SectionWrapper>
	);
};

export default GameweekMemberScreen;
