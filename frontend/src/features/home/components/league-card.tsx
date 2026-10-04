import { ArrowDown, ArrowUp, CopyIcon, CrownIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { useGetInvitationLinkEndpointApiV1LeaguesSlugInvitationLinkGet } from "@/api/invitations/invitations";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";
import type { ApiError } from "@/config/api/api-error";
import {
	type LeagueInvitationLinkResponse,
	type LeagueListItemResponse,
	LeagueStatus,
} from "@/types/schemas";

type Props = {
	league?: LeagueListItemResponse;
	isOwner?: boolean;
	isLoading?: boolean;
};

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const LeagueCard = ({ league, isOwner = false, isLoading }: Props) => {
	const isDraftOwner = league?.status === LeagueStatus.DRAFT && isOwner;
	const invitationQuery =
		useGetInvitationLinkEndpointApiV1LeaguesSlugInvitationLinkGet<
			LeagueInvitationLinkResponse,
			ApiError
		>(league?.slug ?? "", {
			query: {
				enabled: isDraftOwner,
				select: (response) =>
					unwrapResponse(response as unknown as LeagueInvitationLinkResponse),
			},
		});

	if (isLoading) {
		return (
			<Card className="grid gap-0 p-0 md:grid-cols-4">
				{["league", "gameweek", "rank", "leader"].map((stat) => (
					<div
						key={stat}
						className="relative space-y-3 border-t p-4 first:border-t-0 md:border-t-0 md:before:absolute md:before:inset-y-4 md:before:left-0 md:before:w-px md:before:bg-border md:first:before:hidden"
					>
						<Skeleton className="h-4 w-20" />
						<Skeleton className="h-6 w-28" />
					</div>
				))}
			</Card>
		);
	}

	if (!league) return null;

	const initials = league.name
		.split(" ")
		.slice(0, 2)
		.map((word) => word[0])
		.join("")
		.toUpperCase();
	const ownerWon =
		league.gameweek_leader_fpl_entry_id !== null &&
		league.gameweek_leader_fpl_entry_id === league.owner.fpl_entry_id;

	const copyInvitation = async () => {
		if (!invitationQuery.data) return;
		await navigator.clipboard.writeText(invitationQuery.data.invitation_url);
		toast.add({
			title: "Invite link copied",
			type: "success",
		});
	};

	return (
		<Card className="relative grid gap-0 border border-primary/80 p-0 transition-colors hover:border-fpl-pink md:grid-cols-[minmax(0,1.5fr)_minmax(9rem,0.8fr)_minmax(12rem,1fr)_minmax(12rem,1fr)]">
			<Link
				to={`/league/${league.slug}`}
				className="absolute inset-0 z-10 rounded-xl focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
			>
				<span className="sr-only">View {league.name}</span>
			</Link>
			<div className="flex min-w-0 items-center gap-4 p-4">
				<Avatar className="size-14 shrink-0 border-0 after:border-0 sm:size-16">
					<AvatarFallback className="rounded-sm bg-primary/60 text-lg font-semibold">
						{initials}
					</AvatarFallback>
				</Avatar>
				<div className="min-w-0">
					<p className="truncate font-semibold text-lg sm:text-xl">
						{league.name}
					</p>
					<p className="mt-1 text-sm text-muted-foreground">
						{league.member_count}{" "}
						{league.member_count === 1 ? "member" : "members"} ·{" "}
						{isOwner ? "Created by you" : "Member"}
					</p>
				</div>
			</div>

			<div className="relative flex items-center justify-center gap-2 border-t p-4 md:border-t-0 md:before:absolute md:before:inset-y-4 md:before:left-0 md:before:w-px md:before:bg-border">
				<span
					className={`w-fit rounded-sm px-2 py-1 text-xs font-semibold ${
						league.status === LeagueStatus.ACTIVE
							? "bg-success/10 text-success"
							: "bg-fpl-cyan/10 text-fpl-cyan"
					}`}
				>
					{league.status}
				</span>
				<span className="text-muted-foreground text-2xl font-bold">·</span>
				<p className="font-semibold">
					{league.last_scored_gameweek
						? `Gameweek ${league.last_scored_gameweek}`
						: "Not scored"}
				</p>
			</div>

			<div className="relative grid grid-cols-2 border-t md:border-t-0 md:before:absolute md:before:inset-y-4 md:before:left-0 md:before:w-px md:before:bg-border">
				<div className="flex flex-col justify-center p-4">
					<p className="text-sm text-muted-foreground">Your rank</p>
					<div className="mt-1 flex items-baseline gap-2">
						<p className="text-xl font-semibold">{league.rank ?? "—"}</p>
						{league.rank_change !== null && league.rank_change !== 0 && (
							<span
								className={`text-sm font-semibold ${
									league.rank_change > 0 ? "text-success" : "text-destructive"
								}`}
							>
								{league.rank_change > 0 ? <ArrowUp /> : <ArrowDown />}{" "}
								{Math.abs(league.rank_change)}
							</span>
						)}
					</div>
				</div>
				<div className="relative flex flex-col justify-center p-4 before:absolute before:inset-y-4 before:left-0 before:w-px before:bg-border">
					<p className="text-sm text-muted-foreground">Your points</p>
					<p className="mt-1 text-xl font-semibold">
						{league.last_scored_gameweek_points ?? "—"}
					</p>
				</div>
			</div>

			<div className="relative flex min-h-24 items-center border-t p-4 md:border-t-0 md:before:absolute md:before:inset-y-4 md:before:left-0 md:before:w-px md:before:bg-border">
				{league.status === LeagueStatus.DRAFT ? (
					isOwner ? (
						<div className="relative z-20 w-full space-y-2">
							<Button
								type="button"
								size="lg"
								className="w-full"
								onClick={(event) => {
									event.stopPropagation();
									copyInvitation();
								}}
								disabled={!invitationQuery.data || invitationQuery.isPending}
							>
								<CopyIcon />
								Invite members
							</Button>
							{invitationQuery.isError && (
								<p className="text-xs text-destructive" role="alert">
									Could not load invite link.
								</p>
							)}
						</div>
					) : (
						<p className="text-sm text-muted-foreground">
							Invites are managed by the owner.
						</p>
					)
				) : league.gameweek_leader_team_name ? (
					<div className="flex w-full items-center justify-between gap-3">
						<div className="min-w-0">
							<p className="text-sm text-muted-foreground">Gameweek leader</p>
							<p className="mt-1 truncate font-semibold">
								{league.gameweek_leader_team_name}
							</p>
							<p className="text-sm text-muted-foreground">
								{league.gameweek_leader_points} points
							</p>
						</div>
						{ownerWon && (
							<CrownIcon
								className="size-12 shrink-0 text-success"
								aria-label="League owner won this gameweek"
							/>
						)}
					</div>
				) : (
					<p className="text-sm text-muted-foreground">Awaiting results.</p>
				)}
			</div>
		</Card>
	);
};

export default LeagueCard;
