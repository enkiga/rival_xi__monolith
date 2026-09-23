import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import type { GameweekStandingResponse } from "@/types/schemas";

type Props = {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	standing?: GameweekStandingResponse;
	teamName?: string;
	managerName?: string;
	leagueSlug: string;
	gameweek: number;
};

const formatValue = (value: string | number | boolean | null) => {
	if (value === null) return "—";
	if (typeof value === "boolean") return value ? "Yes" : "No";
	return String(value).replaceAll("_", " ");
};

const GameweekTeamDialogue = ({
	open,
	onOpenChange,
	standing,
	teamName,
	managerName,
	leagueSlug,
	gameweek,
}: Props) => {
	if (!standing) return null;

	const details = [
		["Rank", standing.rank],
		["Gross points", standing.gross_points],
		["Transfer deduction", standing.transfer_deduction],
		["Net points", standing.net_points],
		["Scoreboard points", standing.scoreboard_points],
		["Transfers made", standing.transfers_made],
		["Points on bench", standing.points_on_bench],
		["Chip used", standing.chip_used],
		["Chip allowed", standing.chip_allowed],
		["Eligible", standing.eligible],
		["Ineligibility reason", standing.ineligibility_reason],
		["Eligibility status", standing.ineligibility_label],
	] as const;

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="max-h-[85dvh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle>{teamName}</DialogTitle>
					<DialogDescription>{managerName}</DialogDescription>
				</DialogHeader>
				<div className="grid grid-cols-2 gap-x-4 gap-y-3">
					{details.map(([label, value]) => (
						<div key={label}>
							<p className="text-xs text-muted-foreground">{label}</p>
							<p className="font-medium">{formatValue(value)}</p>
						</div>
					))}
				</div>
				<DialogFooter>
					<Button
						render={
							<Link
								to={`/league/${leagueSlug}/gameweek/${gameweek}/member/${standing.league_member_id}`}
							/>
						}
					>
						View Squad
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
};

export default GameweekTeamDialogue;
