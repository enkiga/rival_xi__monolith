import { Button } from "@/components/ui/button";
import type { FPLTeamPreviewResponse } from "@/types/schemas";

const formatNumber = (value: number | null | undefined) =>
	value == null ? "—" : new Intl.NumberFormat().format(value);

type Props = {
	preview: FPLTeamPreviewResponse;
	isClaiming: boolean;
	onClaim: () => void;
	onReject: () => void;
};

const FplTeamPreview = ({ preview, isClaiming, onClaim, onReject }: Props) => (
	<div className="space-y-5 text-center">
		<div>
			<p className="text-lg font-semibold">{preview.team_name}</p>
			<p className="text-sm text-muted-foreground">{preview.manager_name}</p>
		</div>
		<div className="grid grid-cols-2 gap-4 border-y py-4">
			<div>
				<p className="font-semibold">{formatNumber(preview.overall_points)}</p>
				<p className="text-xs text-muted-foreground">Total points</p>
			</div>
			<div>
				<p className="font-semibold">#{formatNumber(preview.overall_rank)}</p>
				<p className="text-xs text-muted-foreground">Overall</p>
			</div>
		</div>
		{preview.available ? (
			<Button
				type="button"
				size="lg"
				className="w-full min-h-10"
				onClick={onClaim}
				disabled={isClaiming}
			>
				{isClaiming ? "Claiming team..." : "Yes, claim this team"}
			</Button>
		) : (
			<p className="text-sm text-destructive">
				This FPL team is already linked to another account.
			</p>
		)}
		<Button
			type="button"
			variant="outline"
			onClick={onReject}
			size="lg"
			className="w-full min-h-10 text-primary"
		>
			That&apos;s not me
		</Button>
	</div>
);

export default FplTeamPreview;
