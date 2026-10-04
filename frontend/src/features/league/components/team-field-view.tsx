import { Skeleton } from "@/components/ui/skeleton";
import type { FPLPlayerPosition, GameweekPickResponse } from "@/types/schemas";
import PlayerKit from "./player-kit";

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
const PlayerMarker = ({ pick }: { pick: GameweekPickResponse }) => (
	<div className="flex min-w-0 flex-col items-center text-center text-white">
		<div className="relative">
			<PlayerKit
				kitUrl={pick.kit_url}
				playerName={pick.player_name}
				className="h-14 w-12 sm:h-20 sm:w-16"
			/>
			{(pick.is_captain || pick.is_vice_captain) && (
				<span className="absolute -right-2 top-0 flex size-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground shadow">
					{pick.is_captain ? "C" : "V"}
				</span>
			)}
		</div>
		<div className="w-20 overflow-hidden rounded-sm bg-black/70 sm:w-28">
			<p className="truncate px-1 text-[10px] font-semibold sm:text-xs">
				{pick.player_name}
			</p>
			<p className="bg-black/35 px-1 text-[9px] sm:text-[10px]">
				{pick.points_contribution} pts
			</p>
		</div>
	</div>
);

const TeamFieldView = ({ picks = [], isLoading = false }: Props) => {
	if (isLoading) {
		return <Skeleton className="min-h-128 sm:min-h-152" />;
	}

	const starters = picks.filter((pick) => pick.is_starter);

	return (
		<section className="relative overflow-hidden rounded-lg border-4 border-emerald-700 bg-emerald-600 px-2 py-6 shadow-inner sm:px-6">
			<div className="pointer-events-none absolute inset-3 border-2 border-white/50" />
			<div className="pointer-events-none absolute left-3 right-3 top-1/2 border-t-2 border-white/50" />
			<div className="pointer-events-none absolute left-1/2 top-1/2 size-20 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white/50 sm:size-28" />

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
		</section>
	);
};

export default TeamFieldView;
