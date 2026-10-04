import { Info } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import type { FPLManagerSearchResult } from "@/types/schemas";

export type SearchState =
	| "idle"
	| "searching"
	| "results"
	| "empty"
	| "unavailable";

type Props = {
	query: string;
	onQueryChange: (value: string) => void;
	searchState: SearchState;
	results: FPLManagerSearchResult[];
	isPreviewing: boolean;
	onSelect: (entryId: string) => void;
	onManualEntry: () => void;
};

const getManagerInitials = (managerName: string) =>
	managerName
		.trim()
		.split(/\s+/)
		.slice(0, 2)
		.map((name) => name.charAt(0))
		.join("")
		.toUpperCase();

const FplTeamSearch = ({
	query,
	onQueryChange,
	searchState,
	results,
	isPreviewing,
	onSelect,
	onManualEntry,
}: Props) => (
	<div className="flex flex-col justify-between">
		<div className="space-y-4">
			<div className="space-y-2">
				<Label htmlFor="manager-search">Your name or team name</Label>
				<Input
					id="manager-search"
					value={query}
					onChange={(event) => onQueryChange(event.target.value)}
					placeholder="Your name or team name"
					maxLength={100}
					autoComplete="off"
					className="w-full min-h-10"
				/>
			</div>
			{searchState === "searching" && (
				<p className="text-sm text-muted-foreground">Searching...</p>
			)}
			{searchState === "results" && (
				<div className="space-y-3" aria-live="polite">
					{results.map((result) => (
						<div
							key={result.entry_id}
							className="flex items-center gap-3 rounded-lg border border-white/20 bg-white/5 p-3"
						>
							<Avatar size="lg">
								<AvatarFallback className="bg-background font-semibold text-primary">
									{getManagerInitials(result.manager_name)}
								</AvatarFallback>
							</Avatar>
							<div className="min-w-0 flex-1">
								<p className="truncate font-medium">{result.team_name}</p>
								<p className="truncate text-sm text-muted-foreground">
									{result.manager_name}
								</p>
							</div>
							<Button
								type="button"
								variant="secondary"
								size="lg"
								onClick={() => onSelect(String(result.entry_id))}
								disabled={isPreviewing}
							>
								Select
							</Button>
						</div>
					))}
				</div>
			)}
			{searchState === "empty" && (
				<p className="text-sm text-muted-foreground">
					No matching FPL teams found.
				</p>
			)}
			{searchState === "unavailable" && (
				<p className="text-sm text-muted-foreground" role="status">
					We couldn&apos;t search FPL right now. You can still connect your team
					using your FPL Team ID.
				</p>
			)}
		</div>
		<div>
			<Separator className="my-4 bg-white" />
			<div className="flex flex-col lg:flex-row justify-between items-center w-full gap-3">
				<div className="flex flex-row gap-2 items-center w-full">
					<Info className="text-muted-foreground size-6" />
					<div className="flex flex-col items-start gap-1">
						<p className="font-semibold">Can&apos;t find your team?</p>
						<p className="text-muted-foreground text-sm">
							Use your FPL Team ID instead.
						</p>
					</div>
				</div>
				<Button
					type="button"
					onClick={onManualEntry}
					size="lg"
					className="w-full lg:w-fit"
				>
					Use Team ID
				</Button>
			</div>
		</div>
	</div>
);

export default FplTeamSearch;
