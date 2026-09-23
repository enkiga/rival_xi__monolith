import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { MemberGameweekResponse } from "@/types/schemas";

type Props = {
	data?: MemberGameweekResponse;
	isLoading?: boolean;
};

const summarySkeletons = ["net", "bench", "transfers"];

const TeamSummary = ({ data, isLoading = false }: Props) => {
	if (isLoading) {
		return (
			<div className="flex gap-4">
				{summarySkeletons.map((item) => (
					<Card key={item} className="flex-1 rounded-none text-center">
						<CardHeader className="justify-items-center">
							<Skeleton className="h-4 w-20" />
						</CardHeader>
						<CardContent className="flex justify-center">
							<Skeleton className="h-8 w-12" />
						</CardContent>
					</Card>
				))}
			</div>
		);
	}

	if (!data) return null;

	const summaries = [
		{ label: "Net points", value: data.net_points },
		{ label: "Bench points", value: data.points_on_bench },
		{ label: "Transfers made", value: data.transfers_made },
	];

	return (
		<section className="flex flex-col gap-4">
			<div className="flex gap-4">
				{summaries.map((summary) => (
					<Card
						key={summary.label}
						className="text-center rounded-none flex-1 flex flex-col justify-between"
					>
						<CardHeader className="justify-items-center">
							<CardTitle className="text-sm text-muted-foreground">
								{summary.label}
							</CardTitle>
						</CardHeader>
						<CardContent className="text-center">
							<p className="text-2xl font-bold">{summary.value}</p>
						</CardContent>
					</Card>
				))}
			</div>
		</section>
	);
};

export default TeamSummary;
