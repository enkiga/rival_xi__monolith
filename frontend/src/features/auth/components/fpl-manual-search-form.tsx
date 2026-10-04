import type { UseFormReturn } from "react-hook-form";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";
import { Button } from "@/components/ui/button";
import type { FPLTeamLookupRequest } from "@/types/schemas";

const manualFields: FormFieldConfig<FPLTeamLookupRequest>[] = [
	{
		name: "reference",
		type: "text",
		label: "FPL team ID or URL",
		placeholder: "Enter your FPL team ID or URL",
		description: "You can find the team ID in your Fantasy Premier League URL.",
		required: true,
	},
];

type Props = {
	form: UseFormReturn<FPLTeamLookupRequest>;
	onSubmit: (values: FPLTeamLookupRequest) => void;
	isSubmitting: boolean;
	onBack: () => void;
};

const FplManualSearchForm = ({
	form,
	onSubmit,
	isSubmitting,
	onBack,
}: Props) => (
	<div className="space-y-6">
		<div className="space-y-2 rounded-lg border border-white/20 bg-white/30 p-4">
			<h2 className="font-semibold">Where can I find my Team ID?</h2>
			<p className="text-sm text-card-foreground/80">
				Log in to the official Fantasy Premier League website, go to
				&quot;Points&quot;, and copy the number from your team&apos;s URL.
			</p>
			<p className="break-all rounded-md bg-background/20 px-3 py-2 font-mono text-xs sm:text-sm">
				fantasy.premierleague.com/entry/1234567/...
			</p>
		</div>
		<AppForm
			form={form}
			onSubmit={onSubmit}
			fields={manualFields}
			submitButtonText="Find team"
			submittingButtonText="Finding team..."
			isSubmitting={isSubmitting}
		/>
		<Button
			type="button"
			variant="outline"
			size="lg"
			onClick={onBack}
			className="w-full min-h-10 text-primary"
		>
			Back to search
		</Button>
	</div>
);

export default FplManualSearchForm;
