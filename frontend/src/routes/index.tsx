import { createBrowserRouter } from "react-router-dom";
import OnboardingPage from "@/features/auth/pages/onboarding";
import OTPVerifyPage from "@/features/auth/pages/otp-verify";
import SignupPage from "@/features/auth/pages/signup";
import HomePage from "@/features/home/pages/homepage";
import InvitationLandingPage from "@/features/invitation/pages/invitation-landing";
import GameweekMemberScreen from "@/features/league/pages/gameweek-member-screen";
import LeagueScreen from "@/features/league/pages/league-screen";
import MainLayout from "@/layouts/main-layout";
import NotFoundPage from "../components/reusable/not-found";

export const router = createBrowserRouter([
	{
		path: "/sign-in",
		element: <SignupPage />,
	},
	{
		path: "/otp-verify",
		element: <OTPVerifyPage />,
	},
	{
		path: "/onboarding",
		element: <OnboardingPage />,
	},
	{
		path: "/invitations/:token",
		element: <InvitationLandingPage />,
	},
	{
		element: <MainLayout />,
		children: [
			{
				index: true,
				element: <HomePage />,
			},
			{
				path: "league/:slug",
				element: <LeagueScreen />,
			},
			{
				path: "league/:slug/gameweek/:gameweek",
				element: <LeagueScreen />,
			},
			{
				path: "league/:slug/gameweek/:gameweek/member/:memberId",
				element: <GameweekMemberScreen />,
			},
		],
	},
	{
		path: "*",
		element: <NotFoundPage />,
	},
]);
