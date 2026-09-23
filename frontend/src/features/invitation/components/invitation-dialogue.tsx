import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
	useAcceptInvitationEndpointApiV1InvitationsTokenAcceptPost,
	usePreviewInvitationEndpointApiV1InvitationsTokenGet,
} from "@/api/invitations/invitations";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import type {
	LeagueInvitationAcceptResponse,
	LeagueInvitationPreviewResponse,
} from "@/types/schemas";
import { INVITATION_STORAGE_KEY } from "../pages/invitation-landing";

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const InvitationDialogue = () => {
	const queryClient = useQueryClient();
	const [token, setToken] = useState(() =>
		sessionStorage.getItem(INVITATION_STORAGE_KEY),
	);
	const [accepted, setAccepted] =
		useState<LeagueInvitationAcceptResponse | null>(null);
	const previewQuery = usePreviewInvitationEndpointApiV1InvitationsTokenGet<
		LeagueInvitationPreviewResponse,
		ApiError
	>(token ?? "", {
		query: {
			enabled: Boolean(token),
			retry: false,
			select: (response) =>
				unwrapResponse(response as unknown as LeagueInvitationPreviewResponse),
		},
	});
	const acceptMutation =
		useAcceptInvitationEndpointApiV1InvitationsTokenAcceptPost<ApiError>({
			mutation: {
				onSuccess: (response) => {
					setAccepted(
						unwrapResponse(
							response as unknown as LeagueInvitationAcceptResponse,
						),
					);
					sessionStorage.removeItem(INVITATION_STORAGE_KEY);
					queryClient.invalidateQueries({ queryKey: ["/api/v1/leagues"] });
				},
			},
		});

	const close = () => {
		sessionStorage.removeItem(INVITATION_STORAGE_KEY);
		setToken(null);
		setAccepted(null);
	};

	if (!token) return null;

	return (
		<Dialog open onOpenChange={(open) => !open && close()}>
			<DialogContent showCloseButton={false} className="lg:min-w-125">
				<DialogHeader>
					<DialogTitle>League invitation</DialogTitle>
					<DialogDescription>
						{accepted
							? `Your request to join ${accepted.league_name} has been submitted.`
							: "Review this invitation before joining the league."}
					</DialogDescription>
				</DialogHeader>

				{previewQuery.isPending ? (
					<div className="space-y-2">
						<Skeleton className="h-5 w-2/3" />
						<Skeleton className="h-4 w-full" />
					</div>
				) : previewQuery.isError ? (
					<p className="text-sm text-destructive" role="alert">
						{previewQuery.error.message}
					</p>
				) : accepted ? (
					<p className="text-sm">
						Membership status: {accepted.membership_status.toLowerCase()}.
					</p>
				) : (
					<div className="space-y-2">
						<p className="text-lg font-semibold">
							{previewQuery.data.league_name}
						</p>
						{previewQuery.data.league_full && (
							<p className="text-sm text-destructive">
								This league is currently full. You can retry this link if space
								becomes available.
							</p>
						)}
						{previewQuery.data.already_member && (
							<p className="text-sm text-muted-foreground">
								You already have a{" "}
								{previewQuery.data.membership_status?.toLowerCase()}
								membership in this league.
							</p>
						)}
					</div>
				)}

				{acceptMutation.isError && (
					<p className="text-sm text-destructive" role="alert">
						{acceptMutation.error.message}
					</p>
				)}

				{previewQuery.data &&
					!accepted &&
					!previewQuery.data.already_member && (
						<Button
							size="lg"
							onClick={() => acceptMutation.mutate({ token })}
							disabled={
								previewQuery.data.league_full || acceptMutation.isPending
							}
						>
							{acceptMutation.isPending ? "Accepting..." : "Accept invitation"}
						</Button>
					)}
				<Button
					variant={!accepted ? "destructive" : "default"}
					size="lg"
					onClick={close}
				>
					{accepted ? "Close" : "Decline"}
				</Button>
			</DialogContent>
		</Dialog>
	);
};

export default InvitationDialogue;
