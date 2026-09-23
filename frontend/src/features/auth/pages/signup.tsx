import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { requestOtpEndpointApiV1AuthOtpRequestPost } from "@/api/auth/auth";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";

import { Card } from "@/components/ui/card";
import { ApiError } from "@/config/api/api-error";
import type { OTPRequest } from "@/types/schemas";
import AuthWrapper from "../components/auth-wrapper";

const OTP_EMAIL_STORAGE_KEY = "rivalxi_otp_email";

const SignupPage = () => {
	const navigate = useNavigate();
	const [requestError, setRequestError] = useState<string | null>(null);
	const form = useForm<OTPRequest>({ defaultValues: { email: "" } });

	const fields: FormFieldConfig<OTPRequest>[] = [
		{
			name: "email",
			type: "email",
			label: "Email address",
			placeholder: "you@example.com",
			autoComplete: "email",
			required: true,
		},
	];

	const handleSubmit = async (values: OTPRequest) => {
		setRequestError(null);
		const email = values.email.trim().toLowerCase();

		try {
			await requestOtpEndpointApiV1AuthOtpRequestPost({ email });
			sessionStorage.setItem(OTP_EMAIL_STORAGE_KEY, email);
			navigate("/otp-verify", { state: { email } });
		} catch (error) {
			setRequestError(
				error instanceof ApiError
					? error.message
					: "We could not send your verification code. Please try again.",
			);
		}
	};

	return (
		<AuthWrapper>
			<Card className="w-full max-w-md p-6 rounded-none">
				<div className="flex flex-col space-y-2 items-center mb-3">
					<h1 className="text-xl font-bold text-card-foreground">
						Welcome to Rival XI
					</h1>
					<p className="mt-2 text-sm text-muted-foreground">
						Enter your email and we&apos;ll send you a verification code.
					</p>
				</div>
				<AppForm
					form={form}
					onSubmit={handleSubmit}
					fields={fields}
					submitButtonText="Send verification code"
					submittingButtonText="Sending code..."
					secondarySection={
						requestError ? (
							<p className="text-center text-sm text-destructive" role="alert">
								{requestError}
							</p>
						) : null
					}
				/>
			</Card>
		</AuthWrapper>
	);
};

export default SignupPage;
