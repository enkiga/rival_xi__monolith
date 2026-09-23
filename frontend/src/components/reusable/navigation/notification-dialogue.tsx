import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
	getGetNotificationsEndpointApiV1NotificationsGetQueryKey,
	getGetUnreadCountEndpointApiV1NotificationsUnreadCountGetQueryKey,
	useMarkNotificationReadEndpointApiV1NotificationsNotificationIdReadPatch,
} from "@/api/notifications/notifications";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import type { ApiError } from "@/config/api/api-error";
import type { NotificationResponse } from "@/types/schemas";

type Props = {
	notification?: NotificationResponse;
	onClose: () => void;
	onNavigate: () => void;
};

const stringData = (value: unknown) =>
	typeof value === "string" ? value : undefined;
const numberData = (value: unknown) =>
	typeof value === "number" ? value : undefined;

const NotificationDialogue = ({ notification, onClose, onNavigate }: Props) => {
	const navigate = useNavigate();
	const queryClient = useQueryClient();
	const markReadMutation =
		useMarkNotificationReadEndpointApiV1NotificationsNotificationIdReadPatch<ApiError>();

	if (!notification) return null;

	const slug = stringData(notification.data.league_slug);
	const gameweek = numberData(notification.data.gameweek);
	const viewPath = (() => {
		switch (notification.type) {
			case "GAMEWEEK_WINNER":
				return slug && gameweek
					? `/league/${slug}/gameweek/${gameweek}`
					: undefined;
			case "LEAGUE_RULES_CHANGED":
				return slug ? `/league/${slug}?dialog=rules` : undefined;
			case "MEMBERSHIP_PENDING":
			case "MEMBERSHIP_APPROVED":
				return slug ? `/league/${slug}?dialog=members` : undefined;
			default:
				return undefined;
		}
	})();

	const refreshNotifications = async () => {
		await Promise.all([
			queryClient.invalidateQueries({
				queryKey: getGetNotificationsEndpointApiV1NotificationsGetQueryKey(),
			}),
			queryClient.invalidateQueries({
				queryKey:
					getGetUnreadCountEndpointApiV1NotificationsUnreadCountGetQueryKey(),
			}),
		]);
	};

	const markAsRead = async () => {
		try {
			if (!notification.read_at) {
				await markReadMutation.mutateAsync({ notificationId: notification.id });
				await refreshNotifications();
			}
			onClose();
		} catch {
			// The mutation error remains visible in the dialogue.
		}
	};

	const viewNotification = async () => {
		if (!viewPath) return;
		try {
			if (!notification.read_at) {
				await markReadMutation.mutateAsync({ notificationId: notification.id });
				await refreshNotifications();
			}
			onClose();
			onNavigate();
			navigate(viewPath);
		} catch {
			// Navigation waits for a successful read confirmation.
		}
	};

	return (
		<Dialog open onOpenChange={(open) => !open && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>{notification.title}</DialogTitle>
					<DialogDescription>{notification.body}</DialogDescription>
				</DialogHeader>
				<div className="space-y-2 text-sm">
					{typeof notification.data.league_name === "string" && (
						<p>
							<span className="font-semibold">League:</span>{" "}
							{notification.data.league_name}
						</p>
					)}
					<time className="block text-muted-foreground">
						{new Intl.DateTimeFormat(undefined, {
							dateStyle: "medium",
							timeStyle: "short",
						}).format(new Date(notification.created_at))}
					</time>
				</div>
				{markReadMutation.isError && (
					<p className="text-sm text-destructive" role="alert">
						{markReadMutation.error.message}
					</p>
				)}
				<DialogFooter>
					<Button
						variant="outline"
						onClick={notification.read_at ? onClose : markAsRead}
						disabled={markReadMutation.isPending}
					>
						{notification.read_at ? "Close" : "Mark as read"}
					</Button>
					{viewPath && (
						<Button
							onClick={viewNotification}
							disabled={markReadMutation.isPending}
						>
							View
						</Button>
					)}
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
};

export default NotificationDialogue;
