import { ArrowLeft } from "lucide-react";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { AuthUserResponse, LeagueDetailResponse } from "@/types/schemas";
import LeagueMembersDialogue from "./league-members-dialogue";
import LeagueRulesDialogue from "./league-rules-dialogue";

type Props = {
	data?: LeagueDetailResponse;
	isLoading?: boolean;
};

const LeagueHeader = ({ data, isLoading = false }: Props) => {
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
	const activeDialog = searchParams.get("dialog");
	const setActiveDialog = (dialog: "members" | "rules", open: boolean) => {
		const nextParams = new URLSearchParams(searchParams);
		if (open) nextParams.set("dialog", dialog);
		else nextParams.delete("dialog");
		setSearchParams(nextParams, { replace: true });
	};

	return (
		<section className="flex items-center justify-between gap-4 border-b border-muted-foreground pb-4">
			<div className="flex items-center gap-4">
				{/* Link back to previous page */}
				<Link to="/">
					<Button size="icon-lg" variant="outline" className="cursor-pointer">
						<ArrowLeft />
					</Button>
				</Link>
				<h2 className="lg:text-2xl text-base font-semibold lg:font-bold">
					{data.name}
				</h2>
				{/* Status if draft show else do not show */}
				{String(data.status).toLowerCase() === "draft" && (
					<span className="rounded-sm bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
						Draft
					</span>
				)}
			</div>
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
		</section>
	);
};

export default LeagueHeader;
