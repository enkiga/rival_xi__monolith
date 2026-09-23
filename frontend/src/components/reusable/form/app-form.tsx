"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
import {
	Controller,
	type ControllerRenderProps,
	type FieldValues,
	type Path,
	type FieldError as ReactHookFormFieldError,
	type SubmitHandler,
	type UseFormReturn,
} from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
	Field,
	FieldContent,
	FieldDescription,
	FieldError,
	FieldGroup,
	FieldLabel,
} from "@/components/ui/field";
import { cn } from "@/lib/utils";
import FormCheckbox from "./inputs/form-checkbox";
import FormChipToggle from "./inputs/form-chip-toggle";
import FormInput from "./inputs/form-input";
import FormOTPInput from "./inputs/form-otp-input";
import FormTextArea from "./inputs/form-textarea";
import type { FormFieldConfig } from "./types";

type Props<TFieldValues extends FieldValues> = {
	id?: string;
	className?: string;
	fieldsClassName?: string;
	form: UseFormReturn<TFieldValues>;
	onSubmit: SubmitHandler<TFieldValues>;
	fields?: FormFieldConfig<TFieldValues>[];
	submitButtonText?: string;
	submittingButtonText?: string;
	isSubmitting?: boolean;
	disabled?: boolean;
	secondarySection?: React.ReactNode;
};

const AppForm = <TFieldValues extends FieldValues>({
	id,
	className,
	fieldsClassName,
	form,
	onSubmit,
	fields,
	submitButtonText = "Submit",
	submittingButtonText = "Submitting...",
	isSubmitting = false,
	disabled = false,
	secondarySection,
}: Props<TFieldValues>) => {
	const [passwordVisibility, setPasswordVisibility] = useState<
		Partial<Record<Path<TFieldValues>, boolean>>
	>({});

	const togglePassword = (fieldName: Path<TFieldValues>) => {
		setPasswordVisibility((prev) => ({
			...prev,
			[fieldName]: !prev[fieldName],
		}));
	};

	const pending = isSubmitting || form.formState.isSubmitting;
	return (
		<form
			id={id}
			onSubmit={form.handleSubmit(onSubmit)}
			className={cn("space-y-6", className)}
		>
			<AppFormFields
				form={form}
				fields={fields ?? []}
				disabled={disabled || pending}
				fieldsClassName={fieldsClassName}
				passwordVisibility={passwordVisibility}
				togglePassword={togglePassword}
			/>

			<Button
				type="submit"
				disabled={disabled || pending}
				size="lg"
				className="w-full min-h-10"
			>
				{pending ? (
					<>
						<Loader2 className="mr-2 h-4 w-4 animate-spin" />
						{submittingButtonText}
					</>
				) : (
					submitButtonText
				)}
			</Button>
			{secondarySection}
		</form>
	);
};

export function AppFormFields<TFieldValues extends FieldValues>({
	form,
	fields,
	fieldsClassName,
	disabled,
	passwordVisibility = {},
	togglePassword,
}: {
	form: UseFormReturn<TFieldValues>;
	fields: FormFieldConfig<TFieldValues>[];
	disabled?: boolean;
	fieldsClassName?: string;
	passwordVisibility?: Partial<Record<Path<TFieldValues>, boolean>>;
	togglePassword?: (fieldName: Path<TFieldValues>) => void;
}) {
	const toFieldErrors = (error: ReactHookFormFieldError | undefined) => {
		if (!error) {
			return [];
		}

		const typedErrors = error.types
			? Object.values(error.types).flatMap((value) => {
					if (Array.isArray(value)) {
						return value.filter(
							(message): message is string =>
								typeof message === "string" && message.trim().length > 0,
						);
					}

					return typeof value === "string" && value.trim().length > 0
						? [value]
						: [];
				})
			: [];

		if (typedErrors.length > 0) {
			return typedErrors.map((message) => ({ message }));
		}

		return error.message ? [{ message: error.message }] : [];
	};

	return (
		<FieldGroup className={fieldsClassName}>
			{fields.map((fieldConfig) => (
				<Controller
					key={fieldConfig.key ?? fieldConfig.name}
					control={form.control}
					name={fieldConfig.name}
					rules={
						fieldConfig.required
							? {
									required: `${fieldConfig.label ?? "This field"} is required`,
								}
							: undefined
					}
					render={({ field, fieldState }) => {
						const isToggleType = fieldConfig.type === "checkbox";

						return (
							<Field
								data-invalid={fieldState.invalid}
								orientation={isToggleType ? "horizontal" : "vertical"}
								className={cn("w-full", fieldConfig.className)}
							>
								{!isToggleType &&
									(fieldConfig.label || fieldConfig.labelAccessory) && (
										<div className="flex items-center justify-between gap-3">
											{fieldConfig.label ? (
												<FieldLabel htmlFor={field.name}>
													{fieldConfig.label}
													{fieldConfig.required && (
														<span className="text-destructive">*</span>
													)}
												</FieldLabel>
											) : (
												<span />
											)}
											{fieldConfig.labelAccessory}
										</div>
									)}

								{renderAppFormInput({
									fieldConfig,
									field,
									disabled,
									passwordVisibility,
									togglePassword,
								})}

								{isToggleType && (
									<FieldContent>
										{fieldConfig.label && (
											<FieldLabel htmlFor={field.name}>
												{fieldConfig.label}
												{fieldConfig.required && (
													<span className="text-destructive">*</span>
												)}
											</FieldLabel>
										)}
										{fieldConfig.description && (
											<FieldDescription className="text-xs">
												{fieldConfig.description}
											</FieldDescription>
										)}
										{fieldState.invalid && (
											<FieldError errors={toFieldErrors(fieldState.error)} />
										)}
									</FieldContent>
								)}

								{!isToggleType && fieldConfig.description && (
									<FieldDescription>{fieldConfig.description}</FieldDescription>
								)}
								{!isToggleType && fieldState.invalid && (
									<FieldError errors={toFieldErrors(fieldState.error)} />
								)}
							</Field>
						);
					}}
				/>
			))}
		</FieldGroup>
	);
}

function renderAppFormInput<TFieldValues extends FieldValues>({
	fieldConfig,
	field,
	disabled,
	passwordVisibility,
	togglePassword,
}: {
	fieldConfig: FormFieldConfig<TFieldValues>;
	field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
	disabled?: boolean;
	passwordVisibility: Partial<Record<Path<TFieldValues>, boolean>>;
	togglePassword?: (fieldName: Path<TFieldValues>) => void;
}) {
	const isSubmitting = Boolean(disabled);

	switch (fieldConfig.type) {
		case "input":
		case "text":
		case "email":
		case "password":
		case "number":
			return (
				<FormInput
					fieldConfig={fieldConfig}
					passwordVisibility={passwordVisibility}
					togglePassword={togglePassword ?? (() => undefined)}
					field={field}
					isSubmitting={isSubmitting}
				/>
			);
		case "textarea":
			return (
				<FormTextArea
					fieldConfig={fieldConfig}
					field={field}
					isSubmitting={isSubmitting}
				/>
			);
		case "checkbox":
			return (
				<FormCheckbox
					fieldConfig={fieldConfig}
					field={field}
					isSubmitting={isSubmitting}
				/>
			);
		case "chip-toggle":
			return (
				<FormChipToggle
					fieldConfig={fieldConfig}
					field={field}
					isSubmitting={isSubmitting}
				/>
			);
		case "otp":
			return (
				<FormOTPInput
					fieldConfig={fieldConfig}
					field={field}
					isSubmitting={isSubmitting}
				/>
			);
		default:
			return null;
	}
}

export default AppForm;
