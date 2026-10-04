import { ArrowDown, ArrowUp, Crown, Minus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type {
	GameweekStandingResponse,
	LeagueDetailMemberResponse,
} from "@/types/schemas";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

type Props = {
	standings?: GameweekStandingResponse[];
	previousStandings?: GameweekStandingResponse[];
	members?: LeagueDetailMemberResponse[];
	currentUserEntryId?: number;
	leagueSlug?: string;
	gameweek?: number;
	isLoading?: boolean;
};

const RankMovement = ({
	standing,
	previousStandings,
}: {
	standing: GameweekStandingResponse;
	previousStandings: GameweekStandingResponse[];
}) => {
	const previousRank = previousStandings.find(
		(item) => item.league_member_id === standing.league_member_id,
	)?.rank;
	const movement =
		standing.rank != null && previousRank != null
			? previousRank - standing.rank
			: 0;

	if (movement > 0) {
		return (
			<span className="flex items-center text-xs font-semibold text-success">
				<ArrowUp className="size-3" />
				{movement}
			</span>
		);
	}

	if (movement < 0) {
		return (
			<span className="flex items-center text-xs font-semibold text-destructive">
				<ArrowDown className="size-3" />
				{Math.abs(movement)}
			</span>
		);
	}

	return (
		<Minus className="size-3 text-muted-foreground" aria-label="No change" />
	);
};

// Takes first two words of the manager's name to create initials
const ManagerInitials = ({ name }: { name?: string }) => {
	const initials = name
		?.split(" ")
		.slice(0, 2)
		.map((word) => word[0])
		.join("")
		.toUpperCase();
	return <>{initials ?? "M"}</>;
};
const GameweekLeaderboard = ({
	standings = [],
	previousStandings = [],
	members = [],
	currentUserEntryId,
	leagueSlug = "",
	gameweek = 0,
	isLoading = false,
}: Props) => {
	const navigate = useNavigate();

	if (isLoading) {
		return (
			<div className="overflow-hidden rounded-xl border">
				<div className="grid grid-cols-[5rem_1fr_6rem] gap-4 border-b bg-muted/40 p-4">
					{["rank", "manager", "score"].map((column) => (
						<Skeleton key={column} className="h-4" />
					))}
				</div>
				{["first", "second", "third", "fourth", "fifth"].map((row) => (
					<div
						key={row}
						className="grid grid-cols-[5rem_1fr_6rem] items-center gap-4 border-b p-4 last:border-0"
					>
						<Skeleton className="h-5" />
						<Skeleton className="h-10 w-40 max-w-full" />
						<Skeleton className="h-5" />
					</div>
				))}
			</div>
		);
	}

	return (
		<div className="overflow-hidden rounded-xl border bg-card">
			<Table>
				<TableHeader className="bg-muted/30">
					<TableRow className="hover:bg-transparent">
						<TableHead className="w-28 px-5">#</TableHead>
						<TableHead>Manager</TableHead>
						<TableHead className="w-28 px-5 text-right">Score</TableHead>
					</TableRow>
				</TableHeader>
				<TableBody>
					{standings.length ? (
						standings.map((standing) => {
							const member = members.find(
								(item) => item.id === standing.league_member_id,
							);
							const isCurrentUser =
								standing.fpl_entry_id === currentUserEntryId;
							const isWinner = standing.eligible && standing.rank === 1;
							const destination = `/league/${leagueSlug}/gameweek/${gameweek}/member/${standing.league_member_id}`;

							return (
								<TableRow
									key={standing.league_member_id}
									tabIndex={0}
									role="link"
									onClick={() => navigate(destination)}
									onKeyDown={(event) => {
										if (event.key === "Enter" || event.key === " ") {
											event.preventDefault();
											navigate(destination);
										}
									}}
									className={cn(
										"h-20 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
										!standing.eligible &&
											"bg-destructive/10 hover:bg-destructive/15",
										standing.eligible &&
											isWinner &&
											"bg-success/10 hover:bg-success/15",
										standing.eligible &&
											!isWinner &&
											isCurrentUser &&
											"bg-primary/10 hover:bg-primary/15",
									)}
								>
									<TableCell className="px-5">
										<div className="flex items-center gap-2 font-semibold">
											{isWinner && (
												<Crown
													className="size-4 shrink-0 text-success"
													aria-label="Winner"
												/>
											)}
											<span>{standing.rank ?? "—"}</span>
											<RankMovement
												standing={standing}
												previousStandings={previousStandings}
											/>
										</div>
									</TableCell>
									<TableCell>
										<div className="flex flex-row items-center gap-2">
											<Avatar className="size-12 shrink-0">
												<AvatarFallback>
													<ManagerInitials name={member?.manager_name} />
												</AvatarFallback>
											</Avatar>
											<div className="min-w-0">
												<div className="flex items-center gap-2">
													<p className="truncate font-semibold">
														{member?.manager_name ?? "Manager unavailable"}
													</p>
												</div>
												<p className="truncate text-xs text-muted-foreground">
													{member?.team_name ??
														`Entry ${standing.fpl_entry_id}`}
												</p>
											</div>
										</div>
									</TableCell>
									<TableCell className="px-5 text-right text-base font-semibold">
										{standing.net_points}
									</TableCell>
								</TableRow>
							);
						})
					) : (
						<TableRow>
							<TableCell colSpan={3} className="h-24 text-center">
								No gameweek results available.
							</TableCell>
						</TableRow>
					)}
				</TableBody>
			</Table>
		</div>
	);
};

export default GameweekLeaderboard;
