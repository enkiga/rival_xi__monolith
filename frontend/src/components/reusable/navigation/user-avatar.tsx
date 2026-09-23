import { Avatar, AvatarFallback } from "@/components/ui/avatar";

type Props = {
	userName: string;
};

const UserAvatar = ({ userName }: Props) => {
	const userInitial = userName
		.trim()
		.split(/\s+/)
		.slice(0, 2)
		.map((name) => name.charAt(0))
		.join("")
		.toUpperCase();

	return (
		<Avatar>
			<AvatarFallback>{userInitial}</AvatarFallback>
		</Avatar>
	);
};

export default UserAvatar;
