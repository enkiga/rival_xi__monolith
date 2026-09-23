import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import {
	getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey,
	getGetLeaguesEndpointApiV1LeaguesGetQueryKey,
	useGetLeagueEndpointApiV1LeaguesSlugGet,
	useGetLeagueGameweekEndpointApiV1LeaguesSlugGameweeksGameweekGet,
	useGetLeagueGameweekSummaryEndpointApiV1LeaguesSlugGameweeksGameweekSummaryGet,
	useSyncGameweekEndpointApiV1LeaguesSlugGameweeksGameweekSyncPost,
} from "@/api/leagues/leagues";
import {
	getGetNotificationsEndpointApiV1NotificationsGetQueryKey,
	getGetUnreadCountEndpointApiV1NotificationsUnreadCountGetQueryKey,
} from "@/api/notifications/notifications";
import type { ApiError } from "@/config/api/api-error";
import type {
	AuthUserResponse,
	LeagueDetailResponse,
	LeagueGameweekResponse,
	LeagueGameweekSummaryResponse,
} from "@/types/schemas";
import GameweekLeaderboard from "../components/gameweek-leaderboard";
import GameweekSelect from "../components/gameweek-select";
import GameweekSummary from "../components/gameweek-summary";
import LeagueActivate from "../components/league-activate";
import LeagueHeader from "../components/league-header";
import LeagueMembershipPending from "../components/league-membership-pending";

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
			<section className="flex flex-col gap-6 py-8">
				<LeagueHeader isLoading />
				<GameweekSelect isLoading />
				<GameweekSummary isLoading />
				<GameweekLeaderboard isLoading />
			</section>
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
		<section className="flex flex-col gap-6 py-8">
			<LeagueHeader data={leagueQuery.data} />
			{String(leagueQuery.data.status).toLowerCase() === "draft" ? (
				<LeagueActivate league={leagueQuery.data} />
			) : (
				<LeagueGameweeks
					league={leagueQuery.data}
					requestedGameweek={gameweek}
				/>
			)}
		</section>
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
	const summaryQuery =
		useGetLeagueGameweekSummaryEndpointApiV1LeaguesSlugGameweeksGameweekSummaryGet<
			LeagueGameweekSummaryResponse,
			ApiError
		>(league.slug, gameweek, {
			query: {
				select: (response) =>
					unwrapResponse(response as unknown as LeagueGameweekSummaryResponse),
			},
		});
	const syncMutation =
		useSyncGameweekEndpointApiV1LeaguesSlugGameweeksGameweekSyncPost<ApiError>();
	const currentEntryId = userQuery.data?.fpl_account?.fpl_entry_id;
	const isOwner = league.members.some(
		(member) =>
			member.role === "OWNER" && member.fpl_entry_id === currentEntryId,
	);
	const resultsMissing =
		standingsQuery.error?.status === 404 || summaryQuery.error?.status === 404;
	const queryError =
		standingsQuery.error?.status !== 404
			? standingsQuery.error
			: summaryQuery.error?.status !== 404
				? summaryQuery.error
				: undefined;
	const status = standingsQuery.data?.status;
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
		<div className="flex flex-col gap-6">
			<GameweekSelect
				gameweek={gameweek}
				startGameweek={league.rules.start_gameweek}
				currentGameweek={league.current_gameweek}
				status={status}
				isOwner={isOwner}
				isSyncing={syncMutation.isPending}
				onChange={selectGameweek}
				onSync={() => void syncGameweek()}
			/>

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

			{standingsQuery.isPending || summaryQuery.isPending ? (
				<>
					<GameweekSummary isLoading />
					<GameweekLeaderboard isLoading />
				</>
			) : resultsMissing ? (
				<div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
					Results have not been synced for gameweek {gameweek}.
				</div>
			) : standingsQuery.data && summaryQuery.data ? (
				<>
					<GameweekSummary summary={summaryQuery.data} />
					<GameweekLeaderboard
						standings={standingsQuery.data.standings}
						members={league.members}
						currentUserEntryId={currentEntryId}
						leagueSlug={league.slug}
						gameweek={gameweek}
					/>
				</>
			) : null}
		</div>
	);
};

export default LeagueScreen;
