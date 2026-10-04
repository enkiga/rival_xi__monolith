import { Clock3Icon } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const LeagueMembershipPending = () => (
	<Card className="px-4 border border-dashed border-fpl-pink flex flex-col lg:items-center text-center p-6 gap-4">
		<div className="bg-primary/50 p-4 rounded-full mx-auto">
			<Clock3Icon />
		</div>
		<h3 className="text-3xl font-semibold">Membership awaiting approval</h3>
		<p className="text-sm text-muted-foreground">
			Your request to join this league has been sent to the league owner. You'll
			be able to view the league once it is approved.
		</p>

		<Button render={<Link to="/" />} variant="outline">
			Back to your leagues
		</Button>
	</Card>
);

export default LeagueMembershipPending;
