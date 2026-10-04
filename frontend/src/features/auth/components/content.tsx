import {
	BookUser,
	LampDesk,
	Lock,
	Settings,
	Trophy,
	UserGroup,
	UserShield,
} from "lucide-react";

export const signInContent = {
	title: "Private FPL leagues for real rivalries",
	description:
		"Create invite-only leagues, compete with friends, and see who takes the crown each gameweek",
	features: [
		{
			icon: <UserGroup />,
			title: "Invite-only leagues",
			description: "Just your friends, your rules",
		},
		{
			icon: <Trophy />,
			title: "Weekly winner",
			description: "See who comes out on top each week",
		},
		{
			icon: <BookUser />,
			title: "Full squad insights",
			description: "Inspect every member's team and score",
		},
		{
			icon: <Settings />,
			title: "Custom rules",
			description: "Choose chips, deductions and more",
		},
	],
};

export const OnboardingContent = {
	title: "Find your FPL team and get started",
	description:
		"Link your official FPL team to join and create leagues in RivalXI, your team will be used across all your leagues",
	features: [
		{
			icon: <LampDesk />,
			title: "Your official FPL team",
			description: "We use official FPL data",
		},
		{
			icon: <UserShield />,
			title: "One team per player",
			description: "Keep league fair and consistent",
		},
		{
			icon: <Lock />,
			title: "Private and secure",
			description: "Only you control your account",
		},
	],
};
