import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { verifyOtpEndpointApiV1AuthOtpVerifyPost } from "@/api/auth/auth";
import heroImage from "@/assets/hero.png";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";
import { Separator } from "@/components/ui/separator";
import { ApiError } from "@/config/api/api-error";
import type { OTPVerifyRequest, OTPVerifyResponse } from "@/types/schemas";
import AuthWrapper from "../components/auth-wrapper";
import { signInContent } from "../components/content";
import PanelContent from "../components/panel-content";

const OTP_EMAIL_STORAGE_KEY = "rivalxi_otp_email";

type OTPFormValues = Pick<OTPVerifyRequest, "code">;

type LocationState = {
	email?: string;
};

const OTPVerifyPage = () => {
	const navigate = useNavigate();
	const location = useLocation();
	const [verifyError, setVerifyError] = useState<string | null>(null);
	const form = useForm<OTPFormValues>({ defaultValues: { code: "" } });
	const locationState = location.state as LocationState | null;
	const email =
		locationState?.email ?? sessionStorage.getItem(OTP_EMAIL_STORAGE_KEY);

	const fields: FormFieldConfig<OTPFormValues>[] = [
		{
			name: "code",
			type: "otp",
			label: "Verification code",
			description: "Enter the six-digit code sent to your email.",
			maxLength: 6,
			required: true,
			autoSubmit: true,
		},
	];

	if (!email) {
		return <Navigate to="/sign-in" replace />;
	}

	const handleSubmit = async (values: OTPFormValues) => {
		setVerifyError(null);

		if (!/^\d{6}$/.test(values.code)) {
			form.setError("code", {
				type: "validate",
				message: "Enter the complete six-digit verification code.",
			});
			return;
		}

		try {
			const response = await verifyOtpEndpointApiV1AuthOtpVerifyPost({
				email,
				code: values.code,
			});
			const payload = response as unknown as
				| OTPVerifyResponse
				| { data: OTPVerifyResponse };
			const user = "data" in payload ? payload.data.user : payload.user;

			sessionStorage.removeItem(OTP_EMAIL_STORAGE_KEY);
			navigate(user.onboarding_required ? "/onboarding" : "/", {
				replace: true,
			});
		} catch (error) {
			setVerifyError(
				error instanceof ApiError
					? error.message
					: "We could not verify your code. Please try again.",
			);
		}
	};

	return (
		<AuthWrapper
			className="flex min-h-144 flex-col justify-between gap-6"
			panelContent={
				<PanelContent
					title={signInContent.title}
					description={signInContent.description}
					features={signInContent.features}
				/>
			}
		>
			<div className="flex flex-col gap-6">
				<div className="mb-3 flex flex-col space-y-2">
					<img
						src={heroImage}
						alt="RivalXI"
						className="mx-auto w-40 md:hidden"
					/>
					<h1 className="text-center text-3xl font-semibold text-card-foreground md:text-start">
						Check your email
					</h1>
					<p className="mx-auto mt-2 max-w-2xs text-center text-sm text-muted-foreground md:mx-0 md:max-w-full md:text-start">
						We sent a 6-digit verification code to {email}.
					</p>
				</div>

				<AppForm
					form={form}
					onSubmit={handleSubmit}
					fields={fields}
					submitButtonText="Verify Code"
					submittingButtonText="Verifying..."
					secondarySection={
						verifyError ? (
							<p className="text-center text-sm text-destructive" role="alert">
								{verifyError}
							</p>
						) : null
					}
				/>
			</div>
			<div className="mt-4">
				<Separator className="my-4" />
				<p className="text-center text-sm text-muted-foreground md:text-start">
					Didn&apos;t receive the code? Check your spam folder. <br />
					<Link
						to="/sign-in"
						onClick={() => sessionStorage.removeItem(OTP_EMAIL_STORAGE_KEY)}
						className="text-primary underline underline-offset-2"
					>
						Try another email
					</Link>
				</p>
			</div>
		</AuthWrapper>
	);
};

export default OTPVerifyPage;
