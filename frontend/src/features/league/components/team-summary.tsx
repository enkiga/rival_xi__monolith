import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { MemberGameweekResponse } from "@/types/schemas";

type Props = {
	data?: MemberGameweekResponse;
	isLoading?: boolean;
};

const summarySkeletons = [
	"gross",
	"deduction",
	"net",
	"transfers",
	"bench",
	"chip",
];

const TeamSummary = ({ data, isLoading = false }: Props) => {
	if (isLoading) {
		return (
			<Card className="grid grid-cols-2 gap-y-6 p-6 sm:grid-cols-3 lg:grid-cols-6">
				{summarySkeletons.map((item) => (
					<div key={item} className="flex flex-col items-center gap-2">
						<Skeleton className="h-8 w-12" />
						<Skeleton className="h-4 w-20" />
					</div>
				))}
			</Card>
		);
	}

	if (!data) return null;

	const summaries = [
		{ label: `GW${data.gameweek} points`, value: data.gross_points },
		{ label: "Transfer deduction", value: data.transfer_deduction },
		{ label: "Net points", value: data.net_points },
		{ label: "Transfers made", value: data.transfers_made },
		{ label: "Points on bench", value: data.points_on_bench },
		{ label: "Chip used", value: data.chip_used ?? "None" },
	];

	return (
		<Card className="grid grid-cols-2 gap-y-6 p-6 sm:grid-cols-3 lg:grid-cols-6">
			{summaries.map((summary, index) => (
				<div
					key={summary.label}
					className={cn(
						"flex min-w-0 flex-col items-center justify-center border-l px-2 text-center",
						index % 2 === 0 && "border-l-0 sm:border-l",
						index % 3 === 0 && "sm:border-l-0 lg:border-l",
						index === 0 && "lg:border-l-0",
					)}
				>
					<p className="text-2xl font-bold">{summary.value}</p>
					<p className="mt-1 text-xs text-muted-foreground sm:text-sm">
						{summary.label}
					</p>
				</div>
			))}
		</Card>
	);
};

export default TeamSummary;
