import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

type Props = {
	gameweek?: number;
	startGameweek?: number;
	currentGameweek?: number;
	status?: string;
	isOwner?: boolean;
	isSyncing?: boolean;
	isLoading?: boolean;
	onChange?: (gameweek: number) => void;
	onSync?: () => void;
};

const GameweekSelect = ({
	gameweek = 0,
	startGameweek = 0,
	currentGameweek = 0,
	status,
	isOwner,
	isSyncing,
	isLoading = false,
	onChange = () => undefined,
	onSync = () => undefined,
}: Props) =>
	isLoading ? (
		<div className="flex flex-col gap-3">
			<div className="flex items-center gap-3">
				<Skeleton className="size-9" />
				<Skeleton className="mx-auto h-7 w-36" />
				<Skeleton className="size-9" />
			</div>
			<Skeleton className="ml-auto h-10 w-36" />
		</div>
	) : (
		<div className="flex flex-col items-center gap-3">
			<div className="flex w-full items-center gap-3">
				<Button
					type="button"
					size="icon-lg"
					variant="outline"
					disabled={gameweek <= startGameweek}
					onClick={() => onChange(gameweek - 1)}
					aria-label="Previous gameweek"
				>
					<ChevronLeft />
				</Button>

				<p className="flex flex-1 items-center justify-center gap-2 px-6 text-center text-lg font-semibold">
					Gameweek {gameweek}
					{status === "LIVE" && (
						<span className="flex items-center gap-1.5 text-xs font-medium text-success">
							<span className="size-2 animate-pulse rounded-full bg-success" />
							Live
						</span>
					)}
				</p>

				<Button
					type="button"
					size="icon-lg"
					variant="outline"
					disabled={gameweek >= currentGameweek}
					onClick={() => onChange(gameweek + 1)}
					aria-label="Next gameweek"
				>
					<ChevronRight />
				</Button>
			</div>

			<div className="flex w-full flex-col lg:ml-auto lg:w-fit">
				{isOwner && (
					<Button size="lg" type="button" onClick={onSync} disabled={isSyncing}>
						<RefreshCw className={isSyncing ? "animate-spin" : undefined} />
						{isSyncing ? "Syncing..." : "Sync gameweek"}
					</Button>
				)}
			</div>
		</div>
	);

export default GameweekSelect;
