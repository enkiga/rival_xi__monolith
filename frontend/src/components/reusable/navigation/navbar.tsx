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
		<section className="bg-primary fixed top-0 w-full left-0 right-0 z-100">
			<SectionWrapper className="flex items-center justify-between p-5">
				<Link to="/">
					<img src={heroImage} alt="Hero" className="h-10 w-auto" />
				</Link>

				<div className="flex space-x-2">
					<NotificationDrawer />
					<ProfileMenu user={user} />
				</div>
			</SectionWrapper>
		</section>
	);
};

export default Navbar;
