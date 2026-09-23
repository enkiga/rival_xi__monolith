import type { ControllerRenderProps, FieldValues, Path } from "react-hook-form";
import type { ChipToggleFieldConfig } from "@/components/reusable/form/types";
import { cn } from "@/lib/utils";

type Props<TFieldValues extends FieldValues> = {
	fieldConfig: ChipToggleFieldConfig<TFieldValues>;
	field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
	isSubmitting: boolean;
};

const FormChipToggle = <TFieldValues extends FieldValues>({
	fieldConfig,
	field,
	isSubmitting,
}: Props<TFieldValues>) => {
	const disabled = fieldConfig.disabled || isSubmitting;
	const selectedValues: string[] = Array.isArray(field.value)
		? field.value.filter(
				(value: unknown): value is string => typeof value === "string",
			)
		: [];

	const isSelected = (value: string) =>
		fieldConfig.multiple
			? selectedValues.includes(value)
			: field.value === value;

	const toggleValue = (value: string) => {
		if (disabled) return;

		if (fieldConfig.multiple) {
			field.onChange(
				selectedValues.includes(value)
					? selectedValues.filter((selected) => selected !== value)
					: [...selectedValues, value],
			);
		} else {
			field.onChange(field.value === value ? undefined : value);
		}

		field.onBlur();
	};

	return (
		<div className={cn("flex flex-wrap gap-2", fieldConfig.inputClassName)}>
			{fieldConfig.options.map((option) => {
				const selected = isSelected(option.value);

				return (
					// biome-ignore lint/a11y/useSemanticElements: The reusable chip is intentionally rendered as a selectable div.
					<div
						key={option.value}
						role="checkbox"
						aria-checked={selected}
						aria-disabled={disabled}
						tabIndex={disabled ? -1 : 0}
						onClick={() => toggleValue(option.value)}
						onKeyDown={(event) => {
							if (event.key === "Enter" || event.key === " ") {
								event.preventDefault();
								toggleValue(option.value);
							}
						}}
						className={cn(
							"cursor-pointer select-none rounded-lg border border-input px-3 py-2 text-sm transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
							selected && "border-primary bg-primary/20 font-semibold",
							disabled && "pointer-events-none cursor-not-allowed opacity-50",
						)}
					>
						{option.label}
					</div>
				);
			})}
		</div>
	);
};

export default FormChipToggle;
