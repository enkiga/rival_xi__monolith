import { Eye, EyeOff } from "lucide-react";
import type { ControllerRenderProps, FieldValues, Path } from "react-hook-form";
import type { InputFieldConfig } from "@/components/reusable/form/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type Props<TFieldValues extends FieldValues> = {
	fieldConfig: InputFieldConfig<TFieldValues>;
	passwordVisibility: Partial<Record<Path<TFieldValues>, boolean>>;
	togglePassword: (fieldName: Path<TFieldValues>) => void;
	field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
	isSubmitting: boolean;
};

const FormInput = <TFieldValues extends FieldValues>(
	props: Props<TFieldValues>,
) => {
	const {
		field,
		fieldConfig,
		isSubmitting,
		passwordVisibility,
		togglePassword,
	} = props;
	const isPasswordType =
		fieldConfig.isPassword || fieldConfig.type === "password";
	const inputType =
		fieldConfig.type === "number"
			? "number"
			: fieldConfig.type === "email"
				? "email"
				: "text";
	const showPassword = passwordVisibility[fieldConfig.name] || false;
	const leftIcon =
		fieldConfig.iconPosition === "left" ? fieldConfig.icon : null;
	const rightIcon =
		fieldConfig.iconPosition === "right" ||
		(!fieldConfig.iconPosition && !isPasswordType)
			? fieldConfig.icon
			: null;

	return (
		<div className="relative flex items-center">
			{/* Left Functional Icon Placement */}
			{leftIcon && (
				<div className="absolute left-3 text-muted-foreground pointer-events-none">
					{leftIcon}
				</div>
			)}

			<Input
				id={field.name}
				type={isPasswordType ? (showPassword ? "text" : "password") : inputType}
				autoComplete={fieldConfig.autoComplete}
				placeholder={fieldConfig.placeholder}
				required={fieldConfig.required}
				disabled={fieldConfig.disabled || isSubmitting}
				className={cn(
					"min-h-10 rounded-sm bg-card",
					leftIcon ? "pl-10" : "",
					rightIcon || isPasswordType ? "pr-10" : "",
					fieldConfig.inputClassName,
				)}
				{...field}
				value={field.value ?? ""}
				onChange={(e) => {
					// Numeric Input logic to scrub non-digit elements out safely
					if (fieldConfig.type === "number") {
						field.onChange(e.target.value === "" ? "" : Number(e.target.value));
					} else if (fieldConfig.isNumericText) {
						const sanitizedValue = e.target.value.replace(/[^0-9.]/g, "");
						field.onChange(sanitizedValue);
					} else {
						field.onChange(e);
					}
				}}
			/>

			{/* Right Dynamic Placement: Custom icons or built-in password context visibility tools */}
			{isPasswordType ? (
				<Button
					size="icon"
					variant="ghost"
					type="button"
					onClick={() => togglePassword(fieldConfig.name)}
					className="absolute right-3 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
				>
					{showPassword ? (
						<EyeOff className="h-4 w-4" />
					) : (
						<Eye className="h-4 w-4" />
					)}
				</Button>
			) : (
				rightIcon && (
					<div className="absolute right-3 text-muted-foreground pointer-events-none">
						{rightIcon}
					</div>
				)
			)}
		</div>
	);
};

export default FormInput;
