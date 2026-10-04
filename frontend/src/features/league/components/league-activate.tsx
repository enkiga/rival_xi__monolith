import { useQueryClient } from "@tanstack/react-query";
import { CircleDashed } from "lucide-react";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import {
	getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey,
	getGetLeaguesEndpointApiV1LeaguesGetQueryKey,
	useActivateLeagueEndpointApiV1LeaguesSlugActivatePatch,
} from "@/api/leagues/leagues";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
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
		<Card className="px-4 border border-dashed border-fpl-pink flex flex-col lg:items-center text-center p-6">
			<div className="bg-primary/50 p-4 rounded-full mx-auto">
				<CircleDashed />
			</div>
			<h3 className="text-3xl font-semibold">Draft League</h3>
			<p className="text-sm text-muted-foreground">
				Review the league settings, then activate it when you are ready.
			</p>
			<div className="flex flex-col lg:flex-row lg:items-center justify-center w-full gap-2 ">
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
		</Card>
	);
};

export default LeagueActivate;
