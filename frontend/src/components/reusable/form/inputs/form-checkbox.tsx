import type { ControllerRenderProps, FieldValues, Path } from "react-hook-form";
import type { CheckboxFieldConfig } from "@/components/reusable/form/types";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

type Props<TFieldValues extends FieldValues> = {
  fieldConfig: CheckboxFieldConfig<TFieldValues>;
  field: ControllerRenderProps<TFieldValues, Path<TFieldValues>>;
  isSubmitting: boolean;
};

const FormCheckbox = <TFieldValues extends FieldValues>(
  props: Props<TFieldValues>,
) => {
  const { fieldConfig, field, isSubmitting } = props;
  return (
    <Checkbox
      id={field.name}
      checked={field.value}
      onCheckedChange={field.onChange}
      disabled={fieldConfig.disabled || isSubmitting}
      className={cn(fieldConfig.inputClassName)}
    />
  );
};

export default FormCheckbox;
