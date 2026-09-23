import {
	ArrowUpDown,
	Calendar,
	ListChecksIcon,
	ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import type { LeagueRulesResponse } from "@/types/schemas";

type Props = {
	rules: LeagueRulesResponse;
	open?: boolean;
	onOpenChange?: (open: boolean) => void;
};

const formatLabel = (value: string) =>
	value
		.toLowerCase()
		.split("_")
		.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
		.join(" ");

const LeagueRulesDialogue = ({ rules, open, onOpenChange }: Props) => {
	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogTrigger render={<Button size="icon-lg" variant="outline" />}>
				<ListChecksIcon />
				<span className="sr-only">View league rules</span>
			</DialogTrigger>
			<DialogContent className="sm:max-w-2xl pt-4 pb-6">
				<DialogHeader className="flex gap-1 border-b pb-2">
					<DialogTitle>
						<ListChecksIcon className="inline-block mr-2" />
						<span className="align-middle text-2xl">League Rules</span>
					</DialogTitle>
					<DialogDescription>
						Review the scoring configuration for this league.
					</DialogDescription>
				</DialogHeader>

				<div className="flex flex-col gap-6">
					<div className="flex items-center gap-2">
						<Calendar className="inline-block" />
						<p className="text-sm text-muted-foreground">
							Scoring Starts From:{" "}
							<span className="font-semibold">
								GWK {rules.start_gameweek}
							</span>{" "}
						</p>
					</div>
					<div className="flex items-center gap-2">
						<ArrowUpDown className="inline-block" />
						<p className="text-sm text-muted-foreground">
							Transfer Deductions:{" "}
							<span className="font-semibold">
								{rules.include_transfer_deductions
									? "Included"
									: "Not Included"}
							</span>
						</p>
					</div>
					<div className="flex flex-col gap-4">
						<div className="flex items-center gap-2 ">
							<ShieldCheck className="inline-block" />
							<p className=" text-sm text-muted-foreground">Allowed Chips:</p>
						</div>
						<div className="flex flex-wrap gap-2 pl-8">
							{rules.allowed_chips.length ? (
								rules.allowed_chips.map((chip) => (
									<span
										key={chip}
										className="rounded-lg border border-primary bg-primary/20 px-3 py-2 text-sm font-semibold text-primary"
									>
										{formatLabel(chip)}
									</span>
								))
							) : (
								<p className="text-sm text-muted-foreground">
									No chips allowed
								</p>
							)}
						</div>
					</div>
				</div>
			</DialogContent>
		</Dialog>
	);
};

export default LeagueRulesDialogue;
