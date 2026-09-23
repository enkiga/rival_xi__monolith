import {
	columnVisibilityFeature,
	createColumnHelper,
	createSortedRowModel,
	rowSortingFeature,
	type SortingState,
	sortFn_alphanumeric,
	sortFn_basic,
	tableFeatures,
	useTable,
} from "@tanstack/react-table";
import { ArrowUpDown, Crown } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type {
	GameweekStandingResponse,
	LeagueDetailMemberResponse,
} from "@/types/schemas";
import GameweekTeamDialogue from "./gameweek-team-dialogue";

type Props = {
	standings?: GameweekStandingResponse[];
	members?: LeagueDetailMemberResponse[];
	currentUserEntryId?: number;
	leagueSlug?: string;
	gameweek?: number;
	isLoading?: boolean;
};

type LeaderboardRow = GameweekStandingResponse & {
	teamName: string;
	managerName: string;
	leagueSlug: string;
	gameweek: number;
};

const features = tableFeatures({
	columnVisibilityFeature,
	rowSortingFeature,
	sortedRowModel: createSortedRowModel(),
	sortFns: {
		alphanumeric: sortFn_alphanumeric,
		basic: sortFn_basic,
	},
});

type LeaderboardFeatures = typeof features;
const columnHelper = createColumnHelper<LeaderboardFeatures, LeaderboardRow>();

const columns = columnHelper.columns([
	columnHelper.accessor("rank", {
		header: ({ column }) => (
			<Button
				variant="ghost"
				className="px-0"
				onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
			>
				Rank <ArrowUpDown className="hidden lg:block" />
			</Button>
		),
		cell: ({ row }) => (
			<div className="flex items-center gap-2 font-semibold">
				{row.original.rank ?? "—"}
				{row.original.rank === 1 && (
					<Crown className="size-4 text-emerald-700" aria-label="Leader" />
				)}
			</div>
		),
	}),
	columnHelper.accessor("teamName", {
		header: "Team",
		cell: ({ row }) => (
			<div>
				<p className="font-semibold">{row.original.teamName}</p>
				<p className="text-xs text-muted-foreground">
					{row.original.managerName}
				</p>
			</div>
		),
	}),
	columnHelper.accessor("scoreboard_points", { header: "Score" }),
	columnHelper.accessor("gross_points", { header: "Gross" }),
	columnHelper.accessor("transfer_deduction", { header: "Deduction" }),
	columnHelper.accessor("net_points", { header: "Net" }),
	columnHelper.accessor("points_on_bench", { header: "Bench" }),
	columnHelper.accessor("chip_used", {
		header: "Chip",
		cell: ({ row }) => row.original.chip_used?.replaceAll("_", " ") ?? "—",
	}),
	columnHelper.accessor("eligible", {
		header: "Status",
		cell: ({ row }) =>
			row.original.eligible
				? "Eligible"
				: (row.original.ineligibility_label ?? "Ineligible"),
	}),
	columnHelper.display({
		id: "actions",
		header: () => <div className="text-right">Action</div>,
		cell: ({ row }) => (
			<div className="flex justify-end">
				<Button
					size="lg"
					variant="outline"
					render={
						<Link
							to={`/league/${row.original.leagueSlug}/gameweek/${row.original.gameweek}/member/${row.original.league_member_id}`}
						/>
					}
				>
					View Squad
				</Button>
			</div>
		),
	}),
]);

const mobileColumns = new Set(["rank", "teamName", "net_points"]);
const skeletonColumns = [
	"rank",
	"team",
	"net",
	"score",
	"gross",
	"deduction",
	"bench",
	"chip",
	"status",
	"action",
];
const skeletonRows = ["first", "second", "third", "fourth", "fifth"];

const columnClassName = (columnId: string) => {
	if (columnId === "rank") return "w-16";
	if (columnId === "teamName") return "w-auto";
	if (columnId === "net_points") return "w-20 lg:w-auto";
	if (columnId === "actions") return "hidden text-right lg:table-cell lg:w-36";
	return mobileColumns.has(columnId) ? undefined : "hidden lg:table-cell";
};

const GameweekLeaderboard = ({
	standings = [],
	members = [],
	currentUserEntryId,
	leagueSlug = "",
	gameweek = 0,
	isLoading = false,
}: Props) => {
	const [sorting, setSorting] = useState<SortingState>([]);
	const [selectedTeam, setSelectedTeam] = useState<LeaderboardRow>();
	const data = useMemo<LeaderboardRow[]>(
		() =>
			standings.map((standing) => {
				const member = members.find(
					(item) => item.id === standing.league_member_id,
				);

				return {
					...standing,
					teamName: member?.team_name ?? `Entry ${standing.fpl_entry_id}`,
					managerName: member?.manager_name ?? "Manager unavailable",
					leagueSlug,
					gameweek,
				};
			}),
		[standings, members, leagueSlug, gameweek],
	);
	const table = useTable({
		features,
		data,
		columns,
		onSortingChange: setSorting,
		state: { sorting },
	});

	if (isLoading) {
		return (
			<div className="overflow-hidden rounded-none">
				<div className="grid grid-cols-[4rem_1fr_5rem] gap-3 border bg-muted p-3 lg:grid-cols-[4rem_repeat(8,1fr)_9rem]">
					{skeletonColumns.map((column, index) => (
						<Skeleton
							key={column}
							className={index > 2 ? "hidden h-4 lg:block" : "h-4"}
						/>
					))}
				</div>
				{skeletonRows.map((row) => (
					<div
						key={row}
						className="grid grid-cols-[4rem_1fr_5rem] items-center gap-3 border-b p-3 lg:grid-cols-[4rem_repeat(8,1fr)_9rem]"
					>
						{skeletonColumns.map((column, cellIndex) => (
							<Skeleton
								key={column}
								className={cellIndex > 2 ? "hidden h-5 lg:block" : "h-5"}
							/>
						))}
					</div>
				))}
			</div>
		);
	}

	return (
		<div className="overflow-hidden rounded-none">
			<Table className="table-fixed">
				<TableHeader className="rounded-t-xl bg-muted [&_th:first-child]:rounded-tl-xl [&_th:last-child]:rounded-tr-xl [&_tr]:border">
					{table.getHeaderGroups().map((headerGroup) => (
						<TableRow key={headerGroup.id}>
							{headerGroup.headers.map((header) => (
								<TableHead
									key={header.id}
									className={columnClassName(header.column.id)}
								>
									{header.isPlaceholder ? null : (
										<table.FlexRender header={header} />
									)}
								</TableHead>
							))}
						</TableRow>
					))}
				</TableHeader>
				<TableBody>
					{table.getRowModel().rows.length ? (
						table.getRowModel().rows.map((row) => {
							const isLeader = row.original.rank === 1;
							const isCurrentUser =
								row.original.fpl_entry_id === currentUserEntryId;

							return (
								<TableRow
									key={row.id}
									onClick={() => {
										if (window.matchMedia("(max-width: 1023px)").matches) {
											setSelectedTeam(row.original);
										}
									}}
									className={`cursor-pointer border-b lg:cursor-default ${
										isLeader
											? "bg-emerald-500/15 hover:bg-emerald-500/25"
											: isCurrentUser
												? "bg-primary/15 hover:bg-primary/25"
												: ""
									}`}
								>
									{row.getVisibleCells().map((cell) => (
										<TableCell
											key={cell.id}
											className={columnClassName(cell.column.id)}
										>
											<table.FlexRender cell={cell} />
										</TableCell>
									))}
								</TableRow>
							);
						})
					) : (
						<TableRow>
							<TableCell colSpan={columns.length} className="h-24 text-center">
								No gameweek results available.
							</TableCell>
						</TableRow>
					)}
				</TableBody>
			</Table>
			<GameweekTeamDialogue
				open={Boolean(selectedTeam)}
				onOpenChange={(open) => {
					if (!open) setSelectedTeam(undefined);
				}}
				standing={selectedTeam}
				teamName={selectedTeam?.teamName}
				managerName={selectedTeam?.managerName}
				leagueSlug={leagueSlug}
				gameweek={gameweek}
			/>
		</div>
	);
};

export default GameweekLeaderboard;
