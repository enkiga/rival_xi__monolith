import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import {
	getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey,
	getGetLeaguesEndpointApiV1LeaguesGetQueryKey,
	useCreateLeagueEndpointApiV1LeaguesPost,
	useUpdateLeagueEndpointApiV1LeaguesSlugPatch,
} from "@/api/leagues/leagues";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import type { ApiError } from "@/config/api/api-error";
import {
	FPLChip,
	type LeagueCreate,
	type LeagueDetailResponse,
} from "@/types/schemas";
import { PlusCircle } from "lucide-react";

type Props = {
	league?: LeagueDetailResponse;
};

const fields: FormFieldConfig<LeagueCreate>[] = [
	{
		name: "name",
		type: "text",
		label: "League name",
		placeholder: "Weekend Rivals",
		required: true,
	},
	{
		name: "rules.start_gameweek",
		type: "number",
		label: "Start gameweek",
		required: true,
	},
	{
		name: "rules.allowed_chips",
		type: "chip-toggle",
		label: "Allowed chips",
		description: "Select all chips that may be used in this league.",
		multiple: true,
		options: [
			{ label: "Wildcard", value: FPLChip.WILDCARD },
			{ label: "Free Hit", value: FPLChip.FREE_HIT },
			{ label: "Bench Boost", value: FPLChip.BENCH_BOOST },
			{ label: "Triple Captain", value: FPLChip.TRIPLE_CAPTAIN },
		],
	},
	{
		name: "rules.include_transfer_deductions",
		type: "checkbox",
		label: "Include transfer deductions",
		description: "Apply FPL transfer costs when calculating league scores.",
	},
];

const getFormValues = (league?: LeagueDetailResponse): LeagueCreate => ({
	name: league?.name ?? "",
	rules: {
		start_gameweek: league?.rules.start_gameweek ?? 1,
		include_transfer_deductions:
			league?.rules.include_transfer_deductions ?? true,
		allowed_chips: league?.rules.allowed_chips ?? [],
	},
});

const LeagueDialog = ({ league }: Props) => {
	const editing = Boolean(league);
	const [open, setOpen] = useState(false);
	const navigate = useNavigate();
	const queryClient = useQueryClient();
	const form = useForm<LeagueCreate>({ defaultValues: getFormValues(league) });

	const finishMutation = async (updatedLeague?: LeagueDetailResponse) => {
		await queryClient.invalidateQueries({
			queryKey: getGetLeaguesEndpointApiV1LeaguesGetQueryKey(),
		});

		if (league) {
			await queryClient.invalidateQueries({
				queryKey: getGetLeagueEndpointApiV1LeaguesSlugGetQueryKey(league.slug),
			});
		}

		form.reset(getFormValues(updatedLeague));
		setOpen(false);

		if (updatedLeague && updatedLeague.slug !== league?.slug) {
			navigate(`/league/${updatedLeague.slug}`, { replace: true });
		}
	};

	const createLeague = useCreateLeagueEndpointApiV1LeaguesPost<ApiError>({
		mutation: {
			onSuccess: () => finishMutation(),
		},
	});
	const updateLeague = useUpdateLeagueEndpointApiV1LeaguesSlugPatch<ApiError>({
		mutation: {
			onSuccess: (response) => {
				const payload = response as unknown as
					| LeagueDetailResponse
					| { data: LeagueDetailResponse };
				return finishMutation("data" in payload ? payload.data : payload);
			},
		},
	});

	const pending = createLeague.isPending || updateLeague.isPending;
	const error = createLeague.error ?? updateLeague.error;

	const handleOpenChange = (nextOpen: boolean) => {
		setOpen(nextOpen);
		if (nextOpen) {
			form.reset(getFormValues(league));
		} else if (!pending) {
			createLeague.reset();
			updateLeague.reset();
		}
	};

	const handleSubmit = (data: LeagueCreate) => {
		if (league) {
			updateLeague.mutate({ slug: league.slug, data });
			return;
		}

		createLeague.mutate({ data });
	};

	return (
		<Dialog open={open} onOpenChange={handleOpenChange}>
			<DialogTrigger
				render={
					<Button size={"lg"} variant={editing ? "outline" : "default"} />
				}
			>
				{!editing && <PlusCircle className="mr-1 size-4" />}
				{editing ? "Edit league" : "Create League"}
			</DialogTrigger>
			<DialogContent className="sm:max-w-lg">
				<DialogHeader>
					<DialogTitle className="text-xl font-semibold">
						{editing ? `Edit ${league?.name}` : "Create a new league"}
					</DialogTitle>
					<DialogDescription>
						Rules cannot be changed after the league becomes active.
					</DialogDescription>
				</DialogHeader>

				<AppForm
					form={form}
					onSubmit={handleSubmit}
					fields={fields}
					isSubmitting={pending}
					submitButtonText={editing ? "Save changes" : "Create league"}
					submittingButtonText={
						editing ? "Saving changes..." : "Creating league..."
					}
					secondarySection={
						error ? (
							<p className="text-center text-sm text-destructive" role="alert">
								{error.message}
							</p>
						) : null
					}
				/>
			</DialogContent>
		</Dialog>
	);
};

export default LeagueDialog;
