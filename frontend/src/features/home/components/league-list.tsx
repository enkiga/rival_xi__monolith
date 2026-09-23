import { CrownIcon } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import { useGetLeaguesEndpointApiV1LeaguesGet } from "@/api/leagues/leagues";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import type {
	AuthUserResponse,
	LeagueListItemResponse,
	LeagueListResponse,
} from "@/types/schemas";

const PAGE_SIZE = 10;
const SKELETON_CARDS = ["first", "second", "third"];
const SKELETON_STATS = ["rank", "gameweek", "members"];

const LeagueList = () => {
	const [page, setPage] = useState(1);
	const userQuery = useGetMeEndpointApiV1AuthMeGet<AuthUserResponse, ApiError>({
		query: {
			select: (response) => {
				const payload = response as unknown as
					| AuthUserResponse
					| { data: AuthUserResponse };
				return "data" in payload ? payload.data : payload;
			},
		},
	});
	const leaguesQuery = useGetLeaguesEndpointApiV1LeaguesGet<
		LeagueListResponse,
		ApiError
	>(
		{ page, page_size: PAGE_SIZE },
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

	if (leaguesQuery.isPending) {
		return (
			<div className="grid gap-4 lg:grid-cols-3">
				{SKELETON_CARDS.map((card) => (
					<LeagueListCard key={card} isLoading />
				))}
			</div>
		);
	}

	if (leaguesQuery.isError) {
		return (
			<p className="text-sm text-destructive" role="alert">
				{leaguesQuery.error.message}
			</p>
		);
	}

	if (!leaguesQuery.data.items.length) {
		return (
			<Card className="px-4">
				<p className="text-sm text-muted-foreground">
					You do not have any leagues yet.
				</p>
			</Card>
		);
	}

	return (
		<div className="flex flex-col gap-4">
			<div className="grid gap-4 lg:grid-cols-3">
				{leaguesQuery.data.items.map((league) => (
					<LeagueListCard
						key={league.slug}
						league={league}
						isOwner={
							userQuery.data?.fpl_account?.fpl_entry_id ===
							league.owner.fpl_entry_id
						}
					/>
				))}
			</div>

			{leaguesQuery.data.pages > 1 && (
				<div className="flex items-center justify-between gap-3">
					<Button
						variant="outline"
						disabled={page === 1}
						onClick={() => setPage((current) => Math.max(1, current - 1))}
					>
						Previous
					</Button>
					<span className="text-sm text-muted-foreground">
						Page {page} of {leaguesQuery.data.pages}
					</span>
					<Button
						variant="outline"
						disabled={page >= leaguesQuery.data.pages}
						onClick={() => setPage((current) => current + 1)}
					>
						Next
					</Button>
				</div>
			)}
		</div>
	);
};

function LeagueListCard({
	league,
	isOwner,
	isLoading = false,
}: {
	league?: LeagueListItemResponse;
	isOwner?: boolean;
	isLoading?: boolean;
}) {
	if (isLoading) {
		return (
			<Card className="h-36 rounded-none">
				<CardHeader className="grid-cols-[1fr_auto]">
					<Skeleton className="h-5 w-36" />
					<Skeleton className="h-6 w-16" />
				</CardHeader>
				<CardContent className="flex justify-between gap-4">
					{SKELETON_STATS.map((stat) => (
						<div key={stat} className="space-y-2">
							<Skeleton className="h-3 w-16" />
							<Skeleton className="h-4 w-10" />
						</div>
					))}
				</CardContent>
			</Card>
		);
	}

	if (!league) return null;

	return (
		<Link to={`/league/${league.slug}`} className="block">
			<Card className="h-full transition-colors hover:ring-primary/50 rounded-none">
				<CardHeader className="grid-cols-[1fr_auto]">
					<CardTitle className="flex items-center gap-2">
						{isOwner && (
							<>
								<CrownIcon className="size-4 text-primary" aria-hidden="true" />
								<span className="sr-only">League owner</span>
							</>
						)}
						{league.name}
					</CardTitle>
					<span className="rounded-sm bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
						{league.status}
					</span>
				</CardHeader>
				<CardContent className="flex flex-row gap-4 justify-between">
					<div>
						<p className="text-muted-foreground">Your rank</p>
						<p className="font-semibold">{league.rank ?? "Unranked"}</p>
					</div>
					<div>
						<p className="text-muted-foreground">Last gameweek</p>
						<p className="font-semibold">
							{league.last_scored_gameweek ?? "Not scored"}
						</p>
					</div>
					<div>
						<p className="text-muted-foreground">Members</p>
						<p className="font-semibold">
							{league.member_count}/{league.max_member_count}
						</p>
					</div>
				</CardContent>
			</Card>
		</Link>
	);
}

export default LeagueList;
