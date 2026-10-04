import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router-dom";
import { useGetMeEndpointApiV1AuthMeGet } from "@/api/auth/auth";
import {
	claimFplTeamEndpointApiV1OnboardingFplClaimPost,
	previewFplTeamEndpointApiV1OnboardingFplPreviewPost,
	searchFplManagersEndpointApiV1OnboardingFplSearchGet,
} from "@/api/onboarding/onboarding";
import heroImage from "@/assets/hero.png";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/config/api/api-error";
import AuthWrapper from "@/features/auth/components/auth-wrapper";
import FplManualSearchForm from "@/features/auth/components/fpl-manual-search-form";
import FplTeamPreview from "@/features/auth/components/fpl-team-preview";
import FplTeamSearch, {
	type SearchState,
} from "@/features/auth/components/fpl-team-search";
import type {
	AuthUserResponse,
	FPLManagerSearchResponse,
	FPLManagerSearchResult,
	FPLTeamLookupRequest,
	FPLTeamPreviewResponse,
} from "@/types/schemas";
import { OnboardingContent } from "../components/content";
import PanelContent from "../components/panel-content";

const unwrapResponse = <T,>(response: T | { data: T }): T =>
	"data" in (response as { data?: T })
		? (response as { data: T }).data
		: (response as T);

const OnboardingPage = () => {
	const navigate = useNavigate();
	const queryClient = useQueryClient();
	const manualForm = useForm<FPLTeamLookupRequest>({
		defaultValues: { reference: "" },
	});
	const [query, setQuery] = useState("");
	const [results, setResults] = useState<FPLManagerSearchResult[]>([]);
	const [searchState, setSearchState] = useState<SearchState>("idle");
	const [showManual, setShowManual] = useState(false);
	const [preview, setPreview] = useState<FPLTeamPreviewResponse | null>(null);
	const [claimReference, setClaimReference] = useState("");
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

	useEffect(() => {
		const normalizedQuery = query.trim();

		if (normalizedQuery.length < 3) {
			return;
		}

		const controller = new AbortController();
		const timer = window.setTimeout(async () => {
			setSearchState("searching");

			try {
				const result =
					await searchFplManagersEndpointApiV1OnboardingFplSearchGet(
						{ q: normalizedQuery },
						{ signal: controller.signal },
					);

				if (controller.signal.aborted) return;
				const response = unwrapResponse(
					result as unknown as FPLManagerSearchResponse,
				);

				if (!response.search_available) {
					setResults([]);
					setSearchState("unavailable");
					return;
				}

				setResults(response.results);
				setSearchState(response.results.length > 0 ? "results" : "empty");
			} catch {
				if (!controller.signal.aborted) {
					setResults([]);
					setSearchState("unavailable");
				}
			}
		}, 400);

		return () => {
			window.clearTimeout(timer);
			controller.abort();
		};
	}, [query]);

	if (userQuery.isPending) {
		return (
			<AuthWrapper className="flex min-h-144 flex-col justify-center gap-6">
				<Skeleton className="mx-auto h-6 w-40" />
				<Skeleton className="h-10 w-full" />
				<Skeleton className="h-10 w-full" />
			</AuthWrapper>
		);
	}

	if (userQuery.isError) {
		return userQuery.error.status === 401 ? (
			<Navigate to="/sign-in" replace />
		) : (
			<AuthWrapper className="flex min-h-144 flex-col justify-center">
				<p className="text-sm text-destructive" role="alert">
					{userQuery.error.message}
				</p>
			</AuthWrapper>
		);
	}

	if (!userQuery.data.onboarding_required) return <Navigate to="/" replace />;

	const previewTeam = async (reference: string) => {
		setError(null);
		setIsPreviewing(true);

		try {
			const response =
				await previewFplTeamEndpointApiV1OnboardingFplPreviewPost({
					reference: reference.trim(),
				});
			setClaimReference(reference.trim());
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
				reference: claimReference,
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
		<AuthWrapper
			className="flex min-h-144 flex-col gap-6"
			panelContent={
				<PanelContent
					title={OnboardingContent.title}
					description={OnboardingContent.description}
					features={OnboardingContent.features}
				/>
			}
		>
			<div className="flex flex-col space-y-2 text-center md:text-start">
				<img src={heroImage} alt="RivalXI" className="mx-auto w-40 md:hidden" />
				<h1 className="text-3xl font-semibold text-card-foreground">
					{preview ? "Is this your team?" : "Find your FPL team"}
				</h1>
				{!preview && (
					<p className="mx-auto mt-2 max-w-2xs text-sm text-muted-foreground md:mx-0 md:max-w-full">
						Search using your name or FPL team name.
					</p>
				)}
			</div>
			<div className="space-y-5">
				{preview ? (
					<FplTeamPreview
						preview={preview}
						isClaiming={isClaiming}
						onClaim={claimTeam}
						onReject={() => {
							setPreview(null);
							setError(null);
						}}
					/>
				) : showManual ? (
					<FplManualSearchForm
						form={manualForm}
						onSubmit={(values) => previewTeam(values.reference)}
						isSubmitting={isPreviewing}
						onBack={() => setShowManual(false)}
					/>
				) : (
					<FplTeamSearch
						query={query}
						onQueryChange={(nextQuery) => {
							setQuery(nextQuery);

							if (nextQuery.trim().length < 3) {
								setResults([]);
								setSearchState("idle");
							}
						}}
						searchState={searchState}
						results={results}
						isPreviewing={isPreviewing}
						onSelect={(entryId) => previewTeam(entryId)}
						onManualEntry={() => setShowManual(true)}
					/>
				)}
				{error && (
					<p className="text-sm text-destructive" role="alert">
						{error}
					</p>
				)}
			</div>
		</AuthWrapper>
	);
};

export default OnboardingPage;
