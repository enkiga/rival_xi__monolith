import z from "zod";

export const envSchema = z.object({
	VITE_API_URL: z.string().url(),
});

export const { VITE_API_URL } = envSchema.parse(import.meta.env);
