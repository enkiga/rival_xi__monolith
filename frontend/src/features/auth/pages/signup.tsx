import { useState } from "react";
import { signInContent } from "../components/content";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { requestOtpEndpointApiV1AuthOtpRequestPost } from "@/api/auth/auth";
import heroImage from "@/assets/hero.png";
import AppForm from "@/components/reusable/form/app-form";
import type { FormFieldConfig } from "@/components/reusable/form/types";
import { Separator } from "@/components/ui/separator";
import { ApiError } from "@/config/api/api-error";
import type { OTPRequest } from "@/types/schemas";
import AuthWrapper from "../components/auth-wrapper";
import PanelContent from "../components/panel-content";

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
						Sign in to Rival XI
					</h1>
					<p className="mx-auto mt-2 max-w-2xs text-center text-sm text-muted-foreground md:mx-0 md:max-w-full md:text-start">
						Enter your email and we&apos;ll send you a verification code to sign
						in.
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
			</div>
			<div>
				<Separator className="my-4" />
				<p className="text-center text-sm text-muted-foreground md:text-start">
					By signing in, you agree to our Terms of Service and Privacy Policy.
				</p>
			</div>
		</AuthWrapper>
	);
};

export default SignupPage;
