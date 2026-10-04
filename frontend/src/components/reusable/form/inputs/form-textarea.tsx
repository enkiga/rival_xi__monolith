import type { ControllerRenderProps, FieldValues, Path } from "react-hook-form";
import type { TextareaFieldConfig } from "@/components/reusable/form/types";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type Props<TFieldValues extends FieldValues> = {
	fieldConfig: TextareaFieldConfig<TFieldValues>;
	field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
	isSubmitting: boolean;
};

const FormTextArea = <TFieldValues extends FieldValues>(
	props: Props<TFieldValues>,
) => {
	const { fieldConfig, isSubmitting, field } = props;
	return (
		<Textarea
			id={field.name}
			placeholder={fieldConfig.placeholder}
			rows={fieldConfig.rows || 3}
			disabled={fieldConfig.disabled || isSubmitting}
			className={cn("bg-card", fieldConfig.inputClassName)}
			{...field}
			value={field.value ?? ""}
		/>
	);
};

export default FormTextArea;
