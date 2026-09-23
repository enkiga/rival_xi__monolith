import { Crown, ListTree, Trophy } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { LeagueGameweekSummaryResponse } from "@/types/schemas";

type Props = {
	summary?: LeagueGameweekSummaryResponse;
	isLoading?: boolean;
};

const summarySkeletons = ["rank", "score", "leader"];

const GameweekSummary = ({ summary, isLoading = false }: Props) => {
	if (isLoading) {
		return (
			<div className="flex gap-4">
				{summarySkeletons.map((item) => (
					<Card key={item} className="flex-1 rounded-none p-4">
						<div className="flex flex-col items-center gap-2 lg:items-start">
							<Skeleton className="h-4 w-16" />
							<Skeleton className="h-8 w-12" />
						</div>
					</Card>
				))}
			</div>
		);
	}

	const isLive = summary?.status === "LIVE";
	const cards = [
		{
			icon: <Trophy />,
			label: "My Rank",
			value: summary?.current_user_rank ?? "—",
		},
		{
			icon: <ListTree />,
			label: "My Score",
			value: summary?.current_user_score ?? "—",
		},
		{
			icon: <Crown />,
			label: isLive ? "Leader" : "Winner",
			value: summary?.winner_score ?? "—",
		},
	];

	return (
		<div className="flex gap-4 ">
			{cards.map((card) => (
				<Card key={card.label} className="flex-1 p-4 rounded-none">
					<div className="flex flex-col lg:flex-row lg:items-center lg:gap-4">
						<div className="lg:block hidden">{card.icon}</div>
						<div className="flex flex-col items-center lg:items-start">
							<h2 className="text-sm text-muted-foreground ">{card.label}</h2>

							<p className="text-2xl font-bold ">{card.value}</p>
						</div>
					</div>
				</Card>
			))}
		</div>
	);
};

export default GameweekSummary;
