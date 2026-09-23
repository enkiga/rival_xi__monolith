import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { verifyOtpEndpointApiV1AuthOtpVerifyPost } from "@/api/auth/auth";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";
import { Card } from "@/components/ui/card";
import { ApiError } from "@/config/api/api-error";
import type { OTPVerifyRequest, OTPVerifyResponse } from "@/types/schemas";
import AuthWrapper from "../components/auth-wrapper";

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
		<AuthWrapper>
			<Card className="w-full max-w-md rounded-none p-6">
				<div className="mb-3 flex flex-col items-center space-y-2 text-center">
					<h1 className="text-xl font-bold text-card-foreground">
						Verify your email
					</h1>
					<p className="text-sm text-muted-foreground">
						We sent a verification code to {email}.
					</p>
				</div>

				<AppForm
					form={form}
					onSubmit={handleSubmit}
					fields={fields}
					submitButtonText="Verify code"
					submittingButtonText="Verifying..."
					secondarySection={
						verifyError ? (
							<p className="text-center text-sm text-destructive" role="alert">
								{verifyError}
							</p>
						) : null
					}
				/>
			</Card>
		</AuthWrapper>
	);
};

export default OTPVerifyPage;
