import { REGEXP_ONLY_DIGITS } from "input-otp";
import type { ControllerRenderProps, FieldValues, Path } from "react-hook-form";
import type { OTPFieldConfig } from "@/components/reusable/form/types";
import {
	InputOTP,
	InputOTPGroup,
	InputOTPSlot,
} from "@/components/ui/input-otp";
import { cn } from "@/lib/utils";

type Props<TFieldValues extends FieldValues> = {
	fieldConfig: OTPFieldConfig<TFieldValues>;
	field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
	isSubmitting: boolean;
	onComplete?: (value: string) => void;
};

const FormOTPInput = <TFieldValues extends FieldValues>({
	fieldConfig,
	field,
	isSubmitting,
	onComplete,
}: Props<TFieldValues>) => {
	const maxLength = fieldConfig.maxLength ?? 6;
	const slots = Array.from({ length: maxLength }, (_, index) => ({
		id: `${field.name}-otp-slot-${index}`,
		index,
	}));

	return (
		<InputOTP
			{...field}
			id={field.name}
			value={typeof field.value === "string" ? field.value : ""}
			maxLength={maxLength}
			pattern={fieldConfig.pattern ?? REGEXP_ONLY_DIGITS}
			inputMode={fieldConfig.inputMode ?? "numeric"}
			autoComplete={fieldConfig.autoComplete ?? "one-time-code"}
			placeholder={fieldConfig.placeholder}
			disabled={fieldConfig.disabled || isSubmitting}
			containerClassName={cn("justify-center", fieldConfig.inputClassName)}
			onComplete={fieldConfig.autoSubmit && onComplete ? onComplete : undefined}
		>
			<InputOTPGroup className="w-full gap-2 lg:gap-4">
				{slots.map((slot) => (
					<InputOTPSlot
						key={slot.id}
						index={slot.index}
						className="aspect-2/3 min-h-12 lg:min-h-15 w-fit flex-1 rounded-lg border"
					/>
				))}
			</InputOTPGroup>
		</InputOTP>
	);
};

export default FormOTPInput;
