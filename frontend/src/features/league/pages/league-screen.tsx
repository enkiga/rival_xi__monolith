import { useQueries, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, RefreshCwOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import {
	getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey,
	getGetLeagueGameweekSummaryEndpointApiV1LeaguesSlugGameweeksGameweekSummaryGetQueryOptions,
	getGetLeaguesEndpointApiV1LeaguesGetQueryKey,
	useGetLeagueEndpointApiV1LeaguesSlugGet,
	useGetLeagueGameweekEndpointApiV1LeaguesSlugGameweeksGameweekGet,
	useSyncGameweekEndpointApiV1LeaguesSlugGameweeksGameweekSyncPost,
} from "@/api/leagues/leagues";
import {
	getGetNotificationsEndpointApiV1NotificationsGetQueryKey,
	getGetUnreadCountEndpointApiV1NotificationsUnreadCountGetQueryKey,
} from "@/api/notifications/notifications";
import SectionWrapper from "@/components/reusable/section-wrapper";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/config/api/api-error";
import type {
	AuthUserResponse,
	LeagueDetailResponse,
	LeagueGameweekResponse,
	LeagueGameweekSummaryResponse,
} from "@/types/schemas";
import GameweekLeaderboard from "../components/gameweek-leaderboard";
import GameweekSelect from "../components/gameweek-select";
import LeagueActivate from "../components/league-activate";
import LeagueHeader from "../components/league-header";
import LeagueMembershipPending from "../components/league-membership-pending";
import { Card } from "@/components/ui/card";

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const LeagueScreen = () => {
	const { slug, gameweek } = useParams<{ slug: string; gameweek?: string }>();
	const leagueQuery = useGetLeagueEndpointApiV1LeaguesSlugGet<
		LeagueDetailResponse,
		ApiError
	>(slug ?? "", {
		query: {
			enabled: Boolean(slug),
			select: (response) =>
				unwrapResponse(response as unknown as LeagueDetailResponse),
		},
	});

	if (!slug) {
		return <p className="text-sm text-destructive">League slug is missing.</p>;
	}

	if (leagueQuery.isPending) {
		return (
			<SectionWrapper className="flex flex-col gap-6 py-8">
				<LeagueHeader isLoading />
				<GameweekSelect isLoading />
				<GameweekLeaderboard isLoading />
			</SectionWrapper>
		);
	}

	if (leagueQuery.isError) {
		if (
			leagueQuery.error.status === 403 &&
			leagueQuery.error.message ===
				"Your league membership is awaiting approval"
		) {
			return <LeagueMembershipPending />;
		}

		return (
			<p className="text-sm text-destructive" role="alert">
				{leagueQuery.error.message}
			</p>
		);
	}

	return (
		<SectionWrapper className="flex flex-col gap-6 py-8">
			{String(leagueQuery.data.status).toLowerCase() === "draft" ? (
				<>
					<LeagueHeader data={leagueQuery.data} />
					<LeagueActivate league={leagueQuery.data} />
				</>
			) : (
				<LeagueGameweeks
					league={leagueQuery.data}
					requestedGameweek={gameweek}
				/>
			)}
		</SectionWrapper>
	);
};

const LeagueGameweeks = ({
	league,
	requestedGameweek,
}: {
	league: LeagueDetailResponse;
	requestedGameweek?: string;
}) => {
	const queryClient = useQueryClient();
	const navigate = useNavigate();
	const location = useLocation();
	const requestedGameweekNumber = Number(requestedGameweek);
	const hasValidRequestedGameweek =
		Number.isInteger(requestedGameweekNumber) &&
		requestedGameweekNumber >= league.rules.start_gameweek &&
		requestedGameweekNumber <= league.current_gameweek;
	const [gameweek, setGameweek] = useState(
		hasValidRequestedGameweek
			? requestedGameweekNumber
			: league.current_gameweek,
	);
	const navigationPending = useRef(false);
	const userQuery = useGetMeEndpointApiV1AuthMeGet<AuthUserResponse, ApiError>({
		query: {
			select: (response) =>
				unwrapResponse(response as unknown as AuthUserResponse),
		},
	});
	const standingsQuery =
		useGetLeagueGameweekEndpointApiV1LeaguesSlugGameweeksGameweekGet<
			LeagueGameweekResponse,
			ApiError
		>(league.slug, gameweek, {
			query: {
				select: (response) =>
					unwrapResponse(response as unknown as LeagueGameweekResponse),
			},
		});
	const startedGameweeks = Array.from(
		{
			length: Math.max(
				0,
				league.current_gameweek - league.rules.start_gameweek + 1,
			),
		},
		(_, index) => league.rules.start_gameweek + index,
	);
	const gameweekSummaryQueries = useQueries({
		queries: startedGameweeks.map((startedGameweek) =>
			getGetLeagueGameweekSummaryEndpointApiV1LeaguesSlugGameweeksGameweekSummaryGetQueryOptions<
				LeagueGameweekSummaryResponse,
				ApiError
			>(league.slug, startedGameweek, {
				query: {
					select: (response) =>
						unwrapResponse(
							response as unknown as LeagueGameweekSummaryResponse,
						),
					staleTime: Number.POSITIVE_INFINITY,
				},
			}),
		),
	});
	const previousStandingsQuery =
		useGetLeagueGameweekEndpointApiV1LeaguesSlugGameweeksGameweekGet<
			LeagueGameweekResponse,
			ApiError
		>(league.slug, gameweek - 1, {
			query: {
				enabled: gameweek > league.rules.start_gameweek,
				select: (response) =>
					unwrapResponse(response as unknown as LeagueGameweekResponse),
			},
		});
	const syncMutation =
		useSyncGameweekEndpointApiV1LeaguesSlugGameweeksGameweekSyncPost<ApiError>();
	const currentEntryId = userQuery.data?.fpl_account?.fpl_entry_id;
	const isOwner = league.members.some(
		(member) =>
			member.role === "OWNER" && member.fpl_entry_id === currentEntryId,
	);
	const resultsMissing = standingsQuery.error?.status === 404;
	const queryError =
		standingsQuery.error?.status !== 404 ? standingsQuery.error : undefined;
	const pointsByGameweek = Object.fromEntries(
		startedGameweeks.map((startedGameweek, index) => [
			startedGameweek,
			gameweekSummaryQueries[index]?.data?.current_user_score ?? null,
		]),
	);
	const statusByGameweek = Object.fromEntries(
		startedGameweeks.map((startedGameweek, index) => [
			startedGameweek,
			gameweekSummaryQueries[index]?.data?.status,
		]),
	);
	const leaguePath = `/league/${league.slug}`;

	useEffect(() => {
		if (requestedGameweek && !hasValidRequestedGameweek) {
			navigate(leaguePath, { replace: true });
		}
	}, [requestedGameweek, hasValidRequestedGameweek, navigate, leaguePath]);

	useEffect(() => {
		if (!standingsQuery.data) return;

		const gameweekPath = `${leaguePath}/gameweek/${gameweek}`;
		if (location.pathname !== gameweekPath) {
			navigate(gameweekPath);
		}
		navigationPending.current = false;
	}, [standingsQuery.data, gameweek, leaguePath, location.pathname, navigate]);

	useEffect(() => {
		if (standingsQuery.error?.status !== 404) return;

		if (navigationPending.current) {
			navigationPending.current = false;
			navigate(leaguePath);
			return;
		}

		if (!requestedGameweek) return;

		// Reset a shared URL when that gameweek has no persisted results.
		// biome-ignore lint/nursery/useReactCompiler: URL-driven state must reset after the request resolves.
		setGameweek(league.current_gameweek);
		navigate(leaguePath, { replace: true });
	}, [
		standingsQuery.error,
		requestedGameweek,
		league.current_gameweek,
		leaguePath,
		navigate,
	]);

	const syncGameweek = async () => {
		await syncMutation.mutateAsync({ slug: league.slug, gameweek });
		const gameweekQueryPrefix = `/api/v1/leagues/${league.slug}/gameweeks/${gameweek}`;

		await Promise.all([
			queryClient.invalidateQueries({
				queryKey: getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey(league.slug),
			}),
			queryClient.invalidateQueries({
				queryKey: getGetLeaguesEndpointApiV1LeaguesGetQueryKey(),
			}),
			queryClient.invalidateQueries({
				queryKey: getGetNotificationsEndpointApiV1NotificationsGetQueryKey(),
			}),
			queryClient.invalidateQueries({
				queryKey:
					getGetUnreadCountEndpointApiV1NotificationsUnreadCountGetQueryKey(),
			}),
			queryClient.invalidateQueries({
				predicate: (query) =>
					typeof query.queryKey[0] === "string" &&
					query.queryKey[0].startsWith(gameweekQueryPrefix),
			}),
		]);
	};

	const selectGameweek = (nextGameweek: number) => {
		navigationPending.current = true;
		setGameweek(nextGameweek);
	};

	return (
		<SectionWrapper className="flex flex-col gap-6">
			<LeagueHeader
				data={league}
				gameweek={gameweek}
				gameweekStatus={statusByGameweek[gameweek]}
			/>
			<GameweekSelect
				gameweek={gameweek}
				startGameweek={league.rules.start_gameweek}
				currentGameweek={league.current_gameweek}
				pointsByGameweek={pointsByGameweek}
				statusByGameweek={statusByGameweek}
				onChange={selectGameweek}
			/>
			{isOwner && (
				<div className="flex justify-end">
					<Button
						size="lg"
						type="button"
						onClick={() => void syncGameweek()}
						disabled={syncMutation.isPending}
					>
						<RefreshCw
							className={syncMutation.isPending ? "animate-spin" : undefined}
						/>
						{syncMutation.isPending ? "Syncing..." : "Sync gameweek"}
					</Button>
				</div>
			)}

			{syncMutation.isError && (
				<p className="text-sm text-destructive" role="alert">
					{syncMutation.error.message}
				</p>
			)}
			{queryError && (
				<p className="text-sm text-destructive" role="alert">
					{queryError.message}
				</p>
			)}

			{standingsQuery.isPending ? (
				<GameweekLeaderboard isLoading />
			) : resultsMissing ? (
				<Card className="px-4 border border-dashed border-fpl-pink flex flex-col lg:items-center text-center p-6">
					<div className="bg-primary/50 p-4 rounded-full mx-auto">
						<RefreshCwOff />
					</div>
					<h3 className="text-3xl font-semibold">Results not synced</h3>
					<p className="text-sm text-muted-foreground">
						Results have not been synced for gameweek {gameweek}.
					</p>
					{isOwner && (
						<Button
							size="lg"
							type="button"
							onClick={() => void syncGameweek()}
							disabled={syncMutation.isPending}
						>
							<RefreshCw
								className={syncMutation.isPending ? "animate-spin" : undefined}
							/>
							{syncMutation.isPending ? "Syncing..." : "Sync gameweek"}
						</Button>
					)}
				</Card>
			) : standingsQuery.data ? (
				<GameweekLeaderboard
					standings={standingsQuery.data.standings}
					previousStandings={previousStandingsQuery.data?.standings}
					members={league.members}
					currentUserEntryId={currentEntryId}
					leagueSlug={league.slug}
					gameweek={gameweek}
				/>
			) : null}
		</SectionWrapper>
	);
};

export default LeagueScreen;
