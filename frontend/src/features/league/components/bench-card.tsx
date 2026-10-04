import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { FPLPlayerPosition, GameweekPickResponse } from "@/types/schemas";
import PlayerKit from "./player-kit";

type Props = {
	picks: GameweekPickResponse[];
	points: number;
};

const positionLabels: Record<FPLPlayerPosition, string> = {
	GOALKEEPER: "GK",
	DEFENDER: "DEF",
	MIDFIELDER: "MID",
	FORWARD: "FWD",
};

const BenchCard = ({ picks, points }: Props) => {
	const substitutes = picks
		.filter((pick) => !pick.is_starter)
		.toSorted((left, right) => left.squad_position - right.squad_position);

	return (
		<Card>
			<CardHeader>
				<CardTitle>
					Bench <span className="text-primary">({points} pts)</span>
				</CardTitle>
			</CardHeader>
			<CardContent>
				<div className="divide-y">
					{substitutes.map((pick) => (
						<div
							key={pick.element_id}
							className="flex items-center gap-3 py-4 first:pt-0 last:pb-0"
						>
							<PlayerKit
								kitUrl={pick.kit_url}
								playerName={pick.player_name}
								className="h-14 w-12 shrink-0"
							/>
							<p className="min-w-0 flex-1 truncate text-sm font-medium">
								{pick.player_name} ({positionLabels[pick.player_position]})
							</p>
							<p className="shrink-0 text-sm text-muted-foreground">
								{pick.gameweek_points}{" "}
								{pick.gameweek_points === 1 ? "pt" : "pts"}
							</p>
						</div>
					))}
				</div>
			</CardContent>
		</Card>
	);
};

export default BenchCard;
