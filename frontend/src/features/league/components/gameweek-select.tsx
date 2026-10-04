import {
	Carousel,
	CarouselContent,
	CarouselItem,
	CarouselNext,
	CarouselPrevious,
} from "@/components/ui/carousel";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { GameweekResultStatus } from "@/types/schemas";

type Props = {
	gameweek?: number;
	startGameweek?: number;
	currentGameweek?: number;
	pointsByGameweek?: Record<number, number | null>;
	statusByGameweek?: Record<number, GameweekResultStatus | undefined>;
	isLoading?: boolean;
	onChange?: (gameweek: number) => void;
};

const GameweekSelect = ({
	gameweek = 0,
	startGameweek = 0,
	currentGameweek = 0,
	pointsByGameweek = {},
	statusByGameweek = {},
	isLoading = false,
	onChange = () => undefined,
}: Props) => {
	const gameweeks = Array.from(
		{ length: 38 - startGameweek + 1 },
		(_, index) => startGameweek + index,
	);

	if (isLoading) {
		return (
			<div className="flex gap-4 rounded-xl border p-4">
				{["one", "two", "three", "four", "five"].map((item) => (
					<Skeleton key={item} className="h-20 min-w-32 flex-1" />
				))}
			</div>
		);
	}

	return (
		<Carousel
			scrollToIndex={
				gameweek ? Math.max(0, gameweek - startGameweek) : undefined
			}
			aria-label="Gameweeks"
			opts={{ align: "center", containScroll: "trimSnaps" }}
			className="px-0 lg:px-16 py-6"
		>
			<CarouselContent className="-ml-3">
				{gameweeks.map((item) => {
					const isFuture = item > currentGameweek;
					const isSelected = item === gameweek;
					const status = statusByGameweek[item];

					return (
						<CarouselItem
							key={item}
							className="basis-1/4 pl-3 sm:basis-1/6 lg:basis-1/10"
						>
							<button
								type="button"
								disabled={isFuture}
								onClick={() => onChange(item)}
								aria-current={isSelected ? "true" : undefined}
								className={cn(
									"flex h-20 w-full flex-col items-center justify-center gap-1 rounded-xl border bg-background px-3 transition-colors",
									"hover:border-primary/60 disabled:cursor-not-allowed disabled:opacity-40 bg-card",
									isSelected &&
										"border-primary ring-2 ring-primary/30 hover:border-primary",
								)}
							>
								<span className="text-base font-semibold">GW{item}</span>
								{status === "LIVE" ? (
									<span className="flex items-center gap-1.5 text-sm text-muted-foreground">
										<span className="size-2 rounded-full bg-success" />
										Live
									</span>
								) : status === "FINAL" && pointsByGameweek[item] != null ? (
									<span className="text-sm text-muted-foreground">
										{pointsByGameweek[item]} pts
									</span>
								) : null}
							</button>
						</CarouselItem>
					);
				})}
			</CarouselContent>
			<CarouselPrevious className="hidden lg:flex lg:left-0.5 size-10 rounded-xl" />
			<CarouselNext className="hidden lg:flex lg:right-0.5 size-10 rounded-xl" />
		</Carousel>
	);
};

export default GameweekSelect;
