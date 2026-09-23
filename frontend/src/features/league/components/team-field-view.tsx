import { Shirt } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import type { FPLPlayerPosition, GameweekPickResponse } from "@/types/schemas";

type Props = {
	picks?: GameweekPickResponse[];
	isLoading?: boolean;
};

const positionOrder: FPLPlayerPosition[] = [
	"GOALKEEPER",
	"DEFENDER",
	"MIDFIELDER",
	"FORWARD",
];
const benchSkeletons = ["first", "second", "third", "fourth"];

const positionStyles: Record<FPLPlayerPosition, string> = {
	GOALKEEPER: "bg-amber-400 text-amber-950",
	DEFENDER: "bg-cyan-400 text-cyan-950",
	MIDFIELDER: "bg-emerald-400 text-emerald-950",
	FORWARD: "bg-rose-400 text-rose-950",
};

const PlayerMarker = ({
	pick,
	showGameweekPoints = false,
}: {
	pick: GameweekPickResponse;
	showGameweekPoints?: boolean;
}) => (
	<div className="flex min-w-0 flex-col items-center text-center text-white">
		<div className="relative">
			<div
				className={`flex size-10 items-center justify-center rounded-none border-2 border-white/80 shadow-md sm:size-12 ${positionStyles[pick.player_position]}`}
			>
				<Shirt className="size-5 sm:size-6" aria-hidden="true" />
			</div>
			{(pick.is_captain || pick.is_vice_captain) && (
				<span className="absolute -right-2 -top-2 flex size-5 items-center justify-center rounded-none bg-background text-[10px] font-bold text-foreground shadow">
					{pick.is_captain ? "C" : "V"}
				</span>
			)}
		</div>
		<div className="mt-1 w-16 overflow-hidden rounded-none bg-black/65 sm:w-24">
			<p className="truncate px-1 text-[10px] font-semibold sm:text-xs">
				{pick.player_name}
			</p>
			<div className="flex items-center justify-center gap-1 bg-black/35 px-1 text-[9px] sm:text-[10px]">
				<span>{pick.team_short_name}</span>
				<span aria-hidden="true">·</span>
				<span>
					{showGameweekPoints ? pick.gameweek_points : pick.points_contribution}{" "}
					pts
				</span>
			</div>
		</div>
	</div>
);

const TeamFieldView = ({ picks = [], isLoading = false }: Props) => {
	if (isLoading) {
		return (
			<section className="grid gap-4 lg:grid-cols-12">
				<Skeleton className="min-h-128 rounded-none lg:col-span-7 sm:min-h-152" />
				<div className="border p-3 lg:col-span-3">
					<Skeleton className="mb-6 h-5 w-16" />
					<div className="grid grid-cols-4 gap-2 lg:grid-cols-1 lg:gap-10">
						{benchSkeletons.map((item) => (
							<div key={item} className="flex flex-col items-center gap-2">
								<Skeleton className="size-12 rounded-none" />
								<Skeleton className="h-8 w-16 rounded-none sm:w-24" />
							</div>
						))}
					</div>
				</div>
			</section>
		);
	}

	const starters = picks.filter((pick) => pick.is_starter);
	const substitutes = picks
		.filter((pick) => !pick.is_starter)
		.toSorted((left, right) => left.squad_position - right.squad_position);

	return (
		<section className="grid gap-4 lg:grid-cols-12 lg:items-stretch">
			<div className="relative overflow-hidden rounded-none border-4 border-emerald-700 bg-emerald-600 px-2 py-6 shadow-inner sm:px-6 lg:col-span-7">
				<div className="pointer-events-none absolute inset-3 border-2 border-white/50" />
				<div className="pointer-events-none absolute left-3 right-3 top-1/2 border-t-2 border-white/50" />
				<div className="pointer-events-none absolute left-1/2 top-1/2 size-20 -translate-x-1/2 -translate-y-1/2 rounded-none border-2 border-white/50 sm:size-28" />

				<div className="relative z-10 grid min-h-128 grid-rows-4 items-center gap-5 sm:min-h-152">
					{positionOrder.map((position) => {
						const players = starters
							.filter((pick) => pick.player_position === position)
							.toSorted(
								(left, right) => left.squad_position - right.squad_position,
							);

						return (
							<div
								key={position}
								className="flex items-center justify-around gap-1 sm:gap-3"
							>
								{players.map((pick) => (
									<PlayerMarker key={pick.element_id} pick={pick} />
								))}
							</div>
						);
					})}
				</div>
			</div>

			<div className="rounded-none border bg-muted/30 p-3 lg:col-span-3">
				<h2 className="mb-3 text-sm font-semibold">Bench</h2>
				<div className="grid grid-cols-4 gap-2 lg:grid-cols-1 lg:content-around lg:h-[calc(100%-2rem)]">
					{substitutes.map((pick) => (
						<PlayerMarker
							key={pick.element_id}
							pick={pick}
							showGameweekPoints
						/>
					))}
				</div>
			</div>
		</section>
	);
};

export default TeamFieldView;
