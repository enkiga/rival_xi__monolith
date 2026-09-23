import { REGEXP_ONLY_DIGITS } from "input-otp";
import { Fragment } from "react";
import type { ControllerRenderProps, FieldValues, Path } from "react-hook-form";
import type { OTPFieldConfig } from "@/components/reusable/form/types";
import {
	InputOTP,
	InputOTPGroup,
	InputOTPSeparator,
	InputOTPSlot,
} from "@/components/ui/input-otp";
import { cn } from "@/lib/utils";

type Props<TFieldValues extends FieldValues> = {
	fieldConfig: OTPFieldConfig<TFieldValues>;
	field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
	isSubmitting: boolean;
};

const FormOTPInput = <TFieldValues extends FieldValues>({
	fieldConfig,
	field,
	isSubmitting,
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
		>
			<InputOTPGroup>
				{slots.map((slot) => (
					<Fragment key={slot.id}>
						<InputOTPSlot
							index={slot.index}
							className="min-h-10 min-w-10 rounded-lg border"
						/>
						{slot.index < maxLength - 1 && <InputOTPSeparator />}
					</Fragment>
				))}
			</InputOTPGroup>
		</InputOTP>
	);
};

export default FormOTPInput;
