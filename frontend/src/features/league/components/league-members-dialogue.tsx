import { useQueryClient } from "@tanstack/react-query";
import {
	CheckIcon,
	CopyIcon,
	RefreshCwIcon,
	UsersIcon,
	XIcon,
} from "lucide-react";
import { useState } from "react";
import {
	useGetInvitationLinkEndpointApiV1LeaguesSlugInvitationLinkGet,
	useRegenerateInvitationLinkEndpointApiV1LeaguesSlugInvitationLinkRegeneratePost,
} from "@/api/invitations/invitations";
import {
	useApproveMemberEndpointApiV1LeaguesSlugMembersMemberIdApprovePatch,
	useRejectMemberEndpointApiV1LeaguesSlugMembersMemberIdRejectPatch,
} from "@/api/leagues/leagues";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import type { ApiError } from "@/config/api/api-error";
import type {
	LeagueDetailMemberResponse,
	LeagueInvitationLinkResponse,
} from "@/types/schemas";

type Props = {
	members: LeagueDetailMemberResponse[];
	slug: string;
	isOwner: boolean;
	open?: boolean;
	onOpenChange?: (open: boolean) => void;
};

const formatLabel = (value: string) =>
	value
		.toLowerCase()
		.split("_")
		.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
		.join(" ");

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const LeagueMembersDialogue = ({
	members,
	slug,
	isOwner,
	open,
	onOpenChange,
}: Props) => {
	const queryClient = useQueryClient();
	const [copied, setCopied] = useState(false);
	const [memberActionError, setMemberActionError] = useState<string | null>(
		null,
	);
	const [activeMemberId, setActiveMemberId] = useState<number | null>(null);
	const invitationQuery =
		useGetInvitationLinkEndpointApiV1LeaguesSlugInvitationLinkGet<
			LeagueInvitationLinkResponse,
			ApiError
		>(slug, {
			query: {
				enabled: isOwner,
				select: (response) =>
					unwrapResponse(response as unknown as LeagueInvitationLinkResponse),
			},
		});
	const regenerateMutation =
		useRegenerateInvitationLinkEndpointApiV1LeaguesSlugInvitationLinkRegeneratePost<ApiError>(
			{
				mutation: {
					onSuccess: (response) => {
						invitationQuery.refetch();
						setCopied(false);
						return unwrapResponse(
							response as unknown as LeagueInvitationLinkResponse,
						);
					},
				},
			},
		);
	const refreshLeague = async () => {
		setActiveMemberId(null);
		await queryClient.invalidateQueries({
			queryKey: [`/api/v1/leagues/${slug}`],
		});
	};
	const approveMutation =
		useApproveMemberEndpointApiV1LeaguesSlugMembersMemberIdApprovePatch<ApiError>(
			{
				mutation: {
					onSuccess: refreshLeague,
					onError: (error) => {
						setActiveMemberId(null);
						setMemberActionError(error.message);
					},
				},
			},
		);
	const rejectMutation =
		useRejectMemberEndpointApiV1LeaguesSlugMembersMemberIdRejectPatch<ApiError>(
			{
				mutation: {
					onSuccess: refreshLeague,
					onError: (error) => {
						setActiveMemberId(null);
						setMemberActionError(error.message);
					},
				},
			},
		);

	const manageMember = (memberId: number, action: "approve" | "reject") => {
		setMemberActionError(null);
		setActiveMemberId(memberId);
		const variables = { slug, memberId };

		if (action === "approve") approveMutation.mutate(variables);
		else rejectMutation.mutate(variables);
	};

	const copyInvitation = async () => {
		if (!invitationQuery.data) return;
		await navigator.clipboard.writeText(invitationQuery.data.invitation_url);
		setCopied(true);
	};

	const regenerateInvitation = () => {
		if (
			window.confirm(
				"Regenerate this invitation link? The current link will stop working immediately.",
			)
		) {
			regenerateMutation.mutate({ slug });
		}
	};

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogTrigger
				render={
					<Button size="icon-lg" variant="outline" className="relative" />
				}
			>
				<UsersIcon />
				{isOwner && members.some((member) => member.status === "PENDING") && (
					<span className="absolute -right-2 -top-2 flex min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-semibold leading-4 text-accent-foreground">
						{Math.min(
							members.filter((member) => member.status === "PENDING").length,
							9,
						)}
						{members.filter((member) => member.status === "PENDING").length > 9
							? "+"
							: ""}
					</span>
				)}
				<span className="sr-only">View league members</span>
			</DialogTrigger>
			<DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-2xl py-4">
				<DialogHeader>
					<DialogTitle>League members ({members.length})</DialogTitle>
					<DialogDescription>
						View the teams currently associated with this league.
					</DialogDescription>
				</DialogHeader>
				{isOwner && (
					<div className="space-y-2 border-b pb-4">
						<p className="text-sm font-semibold">Invitation link</p>
						{invitationQuery.isError ? (
							<p className="text-sm text-destructive" role="alert">
								{invitationQuery.error.message}
							</p>
						) : (
							<div className="flex flex-col gap-2 sm:flex-row">
								<Button
									className="lg:flex-1"
									onClick={copyInvitation}
									size="lg"
									disabled={!invitationQuery.data || invitationQuery.isPending}
								>
									{copied ? <CheckIcon /> : <CopyIcon />}
									{copied ? "Copied" : "Copy invite link"}
								</Button>
								<Button
									variant="outline"
									size="lg"
									onClick={regenerateInvitation}
									disabled={regenerateMutation.isPending}
								>
									<RefreshCwIcon />
									{regenerateMutation.isPending
										? "Regenerating..."
										: "Regenerate"}
								</Button>
							</div>
						)}
						{regenerateMutation.isError && (
							<p className="text-sm text-destructive" role="alert">
								{regenerateMutation.error.message}
							</p>
						)}
					</div>
				)}

				<div className="flex flex-col gap-3">
					{memberActionError && (
						<p className="text-sm text-destructive" role="alert">
							{memberActionError}
						</p>
					)}
					{members.map((member) => {
						const initials = member.manager_name
							.split(" ")
							.map((name) => name.charAt(0))
							.slice(0, 2)
							.join("")
							.toUpperCase();

						return (
							<div key={member.id} className="rounded-xl border p-4">
								<div className="flex items-start justify-between gap-3">
									<div className="flex min-w-0 items-center gap-3">
										<div className="flex items-center gap-2">
											<p className="text-sm text-muted-foreground">
												{members.indexOf(member) + 1}.
											</p>
											<Avatar size="lg">
												<AvatarFallback>{initials}</AvatarFallback>
											</Avatar>
										</div>
										<div className="min-w-0">
											<p className="truncate font-semibold">
												{member.team_name}
											</p>
											<p className="truncate text-sm text-muted-foreground">
												{member.manager_name}
											</p>
										</div>
									</div>
									{isOwner && member.status === "PENDING" ? (
										<div className="flex shrink-0 gap-2">
											<Button
												size="icon-lg"
												className="bg-success text-primary hover:bg-success/80"
												onClick={() => manageMember(member.id, "approve")}
												disabled={
													activeMemberId !== null ||
													approveMutation.isPending ||
													rejectMutation.isPending
												}
												aria-label={`Approve ${member.team_name}`}
												title="Approve member"
											>
												<CheckIcon />
											</Button>
											<Button
												size="icon-lg"
												variant="destructive"
												onClick={() => manageMember(member.id, "reject")}
												disabled={
													activeMemberId !== null ||
													approveMutation.isPending ||
													rejectMutation.isPending
												}
												aria-label={`Reject ${member.team_name}`}
												title="Reject member"
											>
												<XIcon />
											</Button>
										</div>
									) : (
										<span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
											{member.status === "REJECTED"
												? "Rejected"
												: formatLabel(member.role)}
										</span>
									)}
								</div>
							</div>
						);
					})}
				</div>
			</DialogContent>
		</Dialog>
	);
};

export default LeagueMembersDialogue;
