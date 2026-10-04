import { useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { useState } from "react";
import {
	getGetNotificationsEndpointApiV1NotificationsGetQueryKey,
	getGetUnreadCountEndpointApiV1NotificationsUnreadCountGetQueryKey,
	useGetNotificationsEndpointApiV1NotificationsGet,
	useGetUnreadCountEndpointApiV1NotificationsUnreadCountGet,
	useMarkAllReadEndpointApiV1NotificationsReadAllPatch,
} from "@/api/notifications/notifications";
import {
	Drawer,
	DrawerClose,
	DrawerContent,
	DrawerDescription,
	DrawerFooter,
	DrawerHeader,
	DrawerTitle,
	DrawerTrigger,
} from "@/components/ui/drawer";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiError } from "@/config/api/api-error";
import type {
	NotificationListResponse,
	NotificationResponse,
	NotificationUnreadCountResponse,
} from "@/types/schemas";
import { Button } from "../../ui/button";
import NotificationDialogue from "./notification-dialogue";

const PAGE_SIZE = 20;
const NOTIFICATION_SKELETONS = ["first", "second", "third", "fourth"];

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const NotificationDrawer = () => {
	const queryClient = useQueryClient();
	const [limit, setLimit] = useState(PAGE_SIZE);
	const [open, setOpen] = useState(false);
	const [selectedNotification, setSelectedNotification] =
		useState<NotificationResponse>();
	const notificationsQuery = useGetNotificationsEndpointApiV1NotificationsGet<
		NotificationListResponse,
		ApiError
	>(
		{ unread_only: true, limit, offset: 0 },
		{
			query: {
				select: (response) =>
					unwrapResponse(response as unknown as NotificationListResponse),
			},
		},
	);
	const unreadQuery = useGetUnreadCountEndpointApiV1NotificationsUnreadCountGet<
		NotificationUnreadCountResponse,
		ApiError
	>({
		query: {
			select: (response) =>
				unwrapResponse(response as unknown as NotificationUnreadCountResponse),
		},
	});
	const unreadCount = unreadQuery.data?.unread_count ?? 0;
	const notifications = notificationsQuery.data?.items ?? [];
	const canLoadMore = notifications.length === limit;
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
	const markAllMutation = useMarkAllReadEndpointApiV1NotificationsReadAllPatch<
		ApiError,
		unknown
	>({
		mutation: { onSuccess: refreshNotifications },
	});

	return (
		<Drawer swipeDirection="right" open={open} onOpenChange={setOpen}>
			<DrawerTrigger
				render={
					<Button
						size="icon-lg"
						variant="outline"
						aria-label="Open notifications"
					>
						<span className="relative">
							<Bell />
							{unreadCount > 0 && (
								<span className="absolute -right-2 -top-2 flex min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-semibold leading-4 text-accent-foreground">
									{unreadCount > 9 ? "9+" : unreadCount}
								</span>
							)}
						</span>
					</Button>
				}
			/>
			<DrawerContent className="mt-20">
				<DrawerHeader>
					<DrawerTitle>Notifications</DrawerTitle>
					<DrawerDescription>
						Here are your recent notifications.
					</DrawerDescription>
				</DrawerHeader>

				<div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
					{notificationsQuery.isPending ? (
						NOTIFICATION_SKELETONS.map((skeleton) => (
							<div className="space-y-2" key={skeleton}>
								<Skeleton className="h-4 w-2/3" />
								<Skeleton className="h-3 w-full" />
							</div>
						))
					) : notificationsQuery.isError ? (
						<p className="text-sm text-destructive" role="alert">
							{notificationsQuery.error.message}
						</p>
					) : notifications.length === 0 ? (
						<p className="text-sm text-muted-foreground">
							You have no notifications yet.
						</p>
					) : (
						<>
							{notifications.map((notification) => (
								<button
									type="button"
									key={notification.id}
									className="w-full cursor-pointer border-b pb-3 text-left last:border-b-0"
									onClick={() => setSelectedNotification(notification)}
								>
									<div className="flex items-start gap-2">
										{!notification.read_at && (
											<span
												className="mt-1.5 size-2 shrink-0 rounded-full bg-accent"
												aria-hidden="true"
											/>
										)}
										<div className="min-w-0">
											{notification.type === "GAMEWEEK_WINNER" &&
												typeof notification.data.league_name === "string" && (
													<p className="text-xs font-semibold uppercase tracking-wide text-primary">
														{notification.data.league_name}
													</p>
												)}
											<h3 className="font-semibold">{notification.title}</h3>
											<p className="mt-1 text-sm text-muted-foreground">
												{notification.body}
											</p>
											<time className="mt-2 block text-xs text-muted-foreground">
												{new Intl.DateTimeFormat(undefined, {
													dateStyle: "medium",
													timeStyle: "short",
												}).format(new Date(notification.created_at))}
											</time>
										</div>
									</div>
								</button>
							))}
							{canLoadMore && (
								<Button
									variant="outline"
									onClick={() => setLimit((current) => current + PAGE_SIZE)}
									disabled={notificationsQuery.isFetching}
								>
									{notificationsQuery.isFetching ? "Loading..." : "Load more"}
								</Button>
							)}
						</>
					)}
				</div>

				<DrawerFooter>
					{markAllMutation.isError && (
						<p className="text-sm text-destructive" role="alert">
							{markAllMutation.error.message}
						</p>
					)}
					{unreadCount > 0 && (
						<Button
							onClick={() => markAllMutation.mutate()}
							disabled={markAllMutation.isPending}
						>
							{markAllMutation.isPending
								? "Marking as read..."
								: "Mark all as read"}
						</Button>
					)}
					<DrawerClose render={<Button variant="outline">Close</Button>} />
				</DrawerFooter>
			</DrawerContent>
			<NotificationDialogue
				notification={selectedNotification}
				onClose={() => setSelectedNotification(undefined)}
				onNavigate={() => setOpen(false)}
			/>
		</Drawer>
	);
};

export default NotificationDrawer;
