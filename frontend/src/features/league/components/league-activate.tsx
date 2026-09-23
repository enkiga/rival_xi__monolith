import { useQueryClient } from "@tanstack/react-query";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import {
	getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey,
	getGetLeaguesEndpointApiV1LeaguesGetQueryKey,
	useActivateLeagueEndpointApiV1LeaguesSlugActivatePatch,
} from "@/api/leagues/leagues";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ApiError } from "@/config/api/api-error";
import LeagueDialog from "@/features/home/components/league-dialog";
import {
	type AuthUserResponse,
	type LeagueDetailResponse,
	LeagueMemberRole,
	LeagueStatus,
} from "@/types/schemas";

type Props = {
	league: LeagueDetailResponse;
};

const LeagueActivate = ({ league }: Props) => {
	const queryClient = useQueryClient();
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
	const activateLeague =
		useActivateLeagueEndpointApiV1LeaguesSlugActivatePatch<ApiError>({
			mutation: {
				onSuccess: async () => {
					await Promise.all([
						queryClient.invalidateQueries({
							queryKey: getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey(
								league.slug,
							),
						}),
						queryClient.invalidateQueries({
							queryKey: getGetLeaguesEndpointApiV1LeaguesGetQueryKey(),
						}),
					]);
				},
			},
		});

	const owner = league.members.find(
		(member) => member.role === LeagueMemberRole.OWNER,
	);
	const currentUserOwnsLeague =
		owner?.fpl_entry_id === userQuery.data?.fpl_account?.fpl_entry_id;

	if (league.status !== LeagueStatus.DRAFT || !currentUserOwnsLeague) {
		return null;
	}

	return (
		<Card className="border border-dotted border-primary/60 bg-primary/5 shadow-none ring-0">
			<CardContent className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
				<div>
					<p className="font-semibold">This league is still a draft</p>
					<p className="text-sm text-muted-foreground">
						Review the league settings, then activate it when you are ready.
					</p>
				</div>
				<div className="flex w-full gap-2 sm:w-auto">
					<LeagueDialog league={league} />
					<Button
					size="lg"
						disabled={activateLeague.isPending}
						onClick={() => activateLeague.mutate({ slug: league.slug })}
					>
						{activateLeague.isPending ? "Activating..." : "Activate league"}
					</Button>
				</div>
				{activateLeague.error && (
					<p className="w-full text-sm text-destructive" role="alert">
						{activateLeague.error.message}
					</p>
				)}
			</CardContent>
		</Card>
	);
};

export default LeagueActivate;
