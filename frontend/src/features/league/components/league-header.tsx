import { ArrowLeft } from "lucide-react";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type {
	AuthUserResponse,
	GameweekResultStatus,
	LeagueDetailResponse,
} from "@/types/schemas";
import LeagueMembersDialogue from "./league-members-dialogue";
import LeagueRulesDialogue from "./league-rules-dialogue";

type Props = {
	data?: LeagueDetailResponse;
	isLoading?: boolean;
	gameweek?: number;
	gameweekStatus?: GameweekResultStatus;
};

const badgeStyles = {
	LIVE: "bg-success/10 text-success",
	FINAL: "bg-muted text-muted-foreground",
	DRAFT: "bg-fpl-cyan/10 text-fpl-cyan",
};

const LeagueHeader = ({
	data,
	isLoading = false,
	gameweek,
	gameweekStatus,
}: Props) => {
	const { user } = useOutletContext<{ user: AuthUserResponse }>();
	const [searchParams, setSearchParams] = useSearchParams();
	if (isLoading) {
		return (
			<section className="flex items-center justify-between gap-4 border-b border-muted-foreground pb-4">
				<div className="flex items-center gap-4">
					<Skeleton className="size-9" />
					<Skeleton className="h-7 w-48" />
				</div>
				<div className="flex gap-2">
					<Skeleton className="size-9" />
					<Skeleton className="size-9" />
				</div>
			</section>
		);
	}

	if (!data) return null;
	const isOwner = data.members.some(
		(member) =>
			member.role === "OWNER" &&
			member.fpl_entry_id === user.fpl_account?.fpl_entry_id,
	);
	const isDraft = String(data.status).toLowerCase() === "draft";
	const initials = data.name
		.split(" ")
		.slice(0, 2)
		.map((word) => word[0])
		.join("")
		.toUpperCase();
	const activeDialog = searchParams.get("dialog");
	const setActiveDialog = (dialog: "members" | "rules", open: boolean) => {
		const nextParams = new URLSearchParams(searchParams);
		if (open) nextParams.set("dialog", dialog);
		else nextParams.delete("dialog");
		setSearchParams(nextParams, { replace: true });
	};

	return (
		<>
			<Link to="/">
				<Button
					size="lg"
					variant="outline"
					className="cursor-pointer flex items-center gap-2 mt-2"
				>
					<ArrowLeft /> Back
				</Button>
			</Link>

			<Card className="flex flex-col  gap-4 p-6">
				<div className="flex  items-center justify-between">
					<div className="flex min-w-0 items-center gap-4">
						<Avatar className="size-14 shrink-0 border-0 after:border-0 sm:size-16">
							<AvatarFallback className="rounded-sm bg-primary/60 text-lg font-semibold">
								{initials}
							</AvatarFallback>
						</Avatar>
						<div className="min-w-0">
							<h2 className="truncate text-lg font-semibold sm:text-xl">
								{data.name}
							</h2>
							<p className="mt-1 text-sm text-muted-foreground">
								{data.members.length}{" "}
								{data.members.length === 1 ? "member" : "members"}
							</p>
						</div>
					</div>
					<div className="hidden lg:flex flex-col items-center gap-2">
						{isDraft ? (
							<span
								className={`rounded-sm px-2 py-1 text-xs font-semibold ${badgeStyles.DRAFT}`}
							>
								Draft
							</span>
						) : (
							<>
								{gameweek !== undefined && (
									<p className="font-semibold">Gameweek {gameweek}</p>
								)}
								{gameweekStatus && (
									<span
										className={`rounded-sm px-2 py-1 text-xs font-semibold ${badgeStyles[gameweekStatus]}`}
									>
										{gameweekStatus}
									</span>
								)}
							</>
						)}
					</div>
					<div className="flex flex-wrap items-center justify-between gap-4">
						<div className="flex items-center gap-2">
							<LeagueMembersDialogue
								members={data.members}
								slug={data.slug}
								isOwner={isOwner}
								open={activeDialog === "members"}
								onOpenChange={(open) => setActiveDialog("members", open)}
							/>
							<LeagueRulesDialogue
								rules={data.rules}
								open={activeDialog === "rules"}
								onOpenChange={(open) => setActiveDialog("rules", open)}
							/>
						</div>
					</div>
				</div>
			</Card>
		</>
	);
};

export default LeagueHeader;
