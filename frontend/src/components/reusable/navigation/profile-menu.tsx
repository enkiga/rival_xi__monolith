import { useQueryClient } from "@tanstack/react-query";
import { LogOutIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useLogoutEndpointApiV1AuthLogoutPost } from "@/api/auth/auth";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ApiError } from "@/config/api/api-error";
import type { AuthUserResponse } from "@/types/schemas";
import UserAvatar from "./user-avatar";

const ProfileMenu = ({ user }: { user: AuthUserResponse }) => {
	const navigate = useNavigate();
	const queryClient = useQueryClient();
	const logoutMutation = useLogoutEndpointApiV1AuthLogoutPost<ApiError>({
		mutation: {
			onSuccess: () => {
				queryClient.clear();
				navigate("/sign-in", { replace: true });
			},
		},
	});
	const account = user.fpl_account;

	return (
		<DropdownMenu>
			<DropdownMenuTrigger aria-label="Open account menu">
				<UserAvatar userName={account?.manager_name ?? ""} />
			</DropdownMenuTrigger>
			<DropdownMenuContent align="end" className="w-64 mt-6">
				<DropdownMenuGroup>
					<DropdownMenuLabel className="space-y-1 p-2">
						<p className="truncate font-semibold text-foreground">
							{account?.team_name}
						</p>
						<p className="truncate font-normal">{user.email}</p>
					</DropdownMenuLabel>
				</DropdownMenuGroup>
				<DropdownMenuSeparator />
				{logoutMutation.isError && (
					<p className="px-1.5 py-1 text-xs font-medium text-destructive">
						{logoutMutation.error.message}
					</p>
				)}
				<DropdownMenuItem
					variant="destructive"
					onClick={() => logoutMutation.mutate({ data: {} })}
					disabled={logoutMutation.isPending}
				>
					<LogOutIcon />
					{logoutMutation.isPending ? "Logging out..." : "Log out"}
				</DropdownMenuItem>
			</DropdownMenuContent>
		</DropdownMenu>
	);
};

export default ProfileMenu;
