import { Link } from "react-router-dom";
import heroImage from "@/assets/hero.png";
import type { AuthUserResponse } from "@/types/schemas";
import SectionWrapper from "../section-wrapper";
import NotificationDrawer from "./notification-drawer";
import ProfileMenu from "./profile-menu";

type Props = {
	user: AuthUserResponse;
};

const Navbar = ({ user }: Props) => {
	return (
		<section className="bg-background fixed top-0 w-full left-0 right-0 z-100">
			<SectionWrapper className="flex items-center justify-between p-2">
				<Link to="/">
					<img src={heroImage} alt="Hero" className="h-10 lg:h-14 w-auto" />
				</Link>

				<div className="flex flex-row gap-2">
					<NotificationDrawer />
					<ProfileMenu user={user} />
				</div>
			</SectionWrapper>
		</section>
	);
};

export default Navbar;
