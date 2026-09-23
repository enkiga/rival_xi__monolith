import { Clock3Icon } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const LeagueMembershipPending = () => (
	<section className="flex min-h-[60dvh] items-center justify-center py-8">
		<Card className="w-full max-w-md text-center">
			<CardHeader className="items-center">
				<div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
					<Clock3Icon />
				</div>
				<CardTitle>Membership awaiting approval</CardTitle>
			</CardHeader>
			<CardContent className="space-y-4">
				<p className="text-sm text-muted-foreground">
					Your request to join this league has been sent to the league owner.
					You’ll be able to view the league once it is approved.
				</p>
				<Button render={<Link to="/" />} variant="outline">
					Back to your leagues
				</Button>
			</CardContent>
		</Card>
	</section>
);

export default LeagueMembershipPending;
