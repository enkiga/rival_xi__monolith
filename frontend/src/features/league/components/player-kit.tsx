import { Shirt } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

type Props = {
	kitUrl: string | null;
	playerName: string;
	className?: string;
};

const PlayerKit = ({ kitUrl, playerName, className }: Props) => {
	const [hasImageError, setHasImageError] = useState(false);

	if (!kitUrl || hasImageError) {
		return (
			<div
				className={cn(
					"flex size-14 items-center justify-center text-white",
					className,
				)}
			>
				<Shirt className="size-8" aria-hidden="true" />
			</div>
		);
	}

	return (
		<img
			src={kitUrl}
			alt={`${playerName} kit`}
			className={cn("h-16 w-auto object-contain", className)}
			onError={() => setHasImageError(true)}
		/>
	);
};

export default PlayerKit;
