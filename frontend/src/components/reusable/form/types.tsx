import type { HTMLInputAutoCompleteAttribute, ReactNode } from "react";
import type { FieldValues, Path } from "react-hook-form";

export type FieldType =
	| "input"
	| "text"
	| "email"
	| "password"
	| "number"
	| "textarea"
	| "checkbox"
	| "chip-toggle"
	| "otp";

export interface BaseFieldConfig<TFieldValues extends FieldValues> {
	key?: string;
	name: Path<TFieldValues>;
	label?: string;
	labelAccessory?: ReactNode;
	placeholder?: string;
	description?: string;
	required?: boolean;
	disabled?: boolean;
	className?: string;
	inputClassName?: string;
}

export interface InputFieldConfig<TFieldValues extends FieldValues>
	extends BaseFieldConfig<TFieldValues> {
	type: "input" | "text" | "email" | "password" | "number";
	autoComplete?: HTMLInputAutoCompleteAttribute;
	isPassword?: boolean;
	icon?: ReactNode;
	iconPosition?: "left" | "right";
	isNumericText?: boolean;
}

export interface TextareaFieldConfig<TFieldValues extends FieldValues>
	extends BaseFieldConfig<TFieldValues> {
	type: "textarea";
	rows?: number;
}

export interface CheckboxFieldConfig<TFieldValues extends FieldValues>
	extends BaseFieldConfig<TFieldValues> {
	type: "checkbox";
}

export type ChipToggleOption = {
	label: string;
	value: string;
};

export interface ChipToggleFieldConfig<TFieldValues extends FieldValues>
	extends BaseFieldConfig<TFieldValues> {
	type: "chip-toggle";
	options: ChipToggleOption[];
	multiple?: boolean;
}

export interface OTPFieldConfig<TFieldValues extends FieldValues>
	extends BaseFieldConfig<TFieldValues> {
	type: "otp";
	maxLength?: number;
	pattern?: string;
	inputMode?: "numeric" | "text";
	autoComplete?: HTMLInputAutoCompleteAttribute;
}

export type FormFieldConfig<TFieldValues extends FieldValues> =
	| InputFieldConfig<TFieldValues>
	| TextareaFieldConfig<TFieldValues>
	| CheckboxFieldConfig<TFieldValues>
	| ChipToggleFieldConfig<TFieldValues>
	| OTPFieldConfig<TFieldValues>;
