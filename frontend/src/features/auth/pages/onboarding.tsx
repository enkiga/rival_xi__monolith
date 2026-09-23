import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router-dom";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import {
	claimFplTeamEndpointApiV1OnboardingFplClaimPost,
	previewFplTeamEndpointApiV1OnboardingFplPreviewPost,
} from "@/api/onboarding/onboarding";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/config/api/api-error";
import AuthWrapper from "@/features/auth/components/auth-wrapper";
import type {
	AuthUserResponse,
	FPLTeamLookupRequest,
	FPLTeamPreviewResponse,
} from "@/types/schemas";

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const fields: FormFieldConfig<FPLTeamLookupRequest>[] = [
	{
		name: "reference",
		type: "text",
		label: "FPL team ID or URL",
		placeholder: "Enter your FPL team ID or URL",
		description: "You can find the team ID in your Fantasy Premier League URL.",
		required: true,
	},
];

const OnboardingPage = () => {
	const navigate = useNavigate();
	const queryClient = useQueryClient();
	const form = useForm<FPLTeamLookupRequest>({
		defaultValues: { reference: "" },
	});
	const [preview, setPreview] = useState<FPLTeamPreviewResponse | null>(null);
	const [isPreviewing, setIsPreviewing] = useState(false);
	const [isClaiming, setIsClaiming] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const userQuery = useGetMeEndpointApiV1AuthMeGet<AuthUserResponse, ApiError>({
		query: {
			retry: false,
			select: (response) =>
				unwrapResponse(response as unknown as AuthUserResponse),
		},
	});

	if (userQuery.isPending) {
		return (
			<AuthWrapper>
				<Card className="w-full max-w-md p-6">
					<Skeleton className="mx-auto h-6 w-40" />
					<Skeleton className="h-10 w-full" />
					<Skeleton className="h-10 w-full" />
				</Card>
			</AuthWrapper>
		);
	}

	if (userQuery.isError) {
		return userQuery.error.status === 401 ? (
			<Navigate to="/sign-in" replace />
		) : (
			<AuthWrapper>
				<p className="text-sm text-destructive" role="alert">
					{userQuery.error.message}
				</p>
			</AuthWrapper>
		);
	}

	if (!userQuery.data.onboarding_required) {
		return <Navigate to="/" replace />;
	}

	const previewTeam = async (values: FPLTeamLookupRequest) => {
		setError(null);
		setPreview(null);
		setIsPreviewing(true);

		try {
			const response =
				await previewFplTeamEndpointApiV1OnboardingFplPreviewPost({
					reference: values.reference.trim(),
				});
			setPreview(unwrapResponse(response as unknown as FPLTeamPreviewResponse));
		} catch (previewError) {
			setError(
				previewError instanceof ApiError
					? previewError.message
					: "We could not find that FPL team. Please try again.",
			);
		} finally {
			setIsPreviewing(false);
		}
	};

	const claimTeam = async () => {
		if (!preview?.available) return;

		setError(null);
		setIsClaiming(true);
		try {
			await claimFplTeamEndpointApiV1OnboardingFplClaimPost({
				reference: form.getValues("reference").trim(),
			});
			await queryClient.invalidateQueries({ queryKey: ["/api/v1/auth/me"] });
			navigate("/", { replace: true });
		} catch (claimError) {
			setError(
				claimError instanceof ApiError
					? claimError.message
					: "We could not claim that FPL team. Please try again.",
			);
		} finally {
			setIsClaiming(false);
		}
	};

	return (
		<AuthWrapper>
			<Card className="w-full max-w-md rounded-none p-6">
				<CardHeader className="px-0 text-center">
					<CardTitle>Claim your FPL team</CardTitle>
					<CardDescription>
						Link your Fantasy Premier League team to finish setting up your
						account.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-5 px-0">
					<AppForm
						form={form}
						onSubmit={previewTeam}
						fields={fields}
						submitButtonText="Find team"
						submittingButtonText="Finding team..."
						isSubmitting={isPreviewing}
					/>

					{preview && (
						<div className="space-y-4 border p-4">
							<div>
								<p className="font-semibold">{preview.team_name}</p>
								<p className="text-sm text-muted-foreground">
									{preview.manager_name} · Entry {preview.fpl_entry_id}
								</p>
							</div>
							{preview.available ? (
								<Button
									type="button"
									size="lg"
									className="w-full"
									onClick={claimTeam}
									disabled={isClaiming}
								>
									{isClaiming ? "Claiming team..." : "Claim this team"}
								</Button>
							) : (
								<p className="text-sm text-destructive">
									This FPL team is already linked to another account.
								</p>
							)}
						</div>
					)}

					{error && (
						<p className="text-sm text-destructive" role="alert">
							{error}
						</p>
					)}
				</CardContent>
			</Card>
		</AuthWrapper>
	);
};

export default OnboardingPage;
