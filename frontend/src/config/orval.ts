import { defineConfig } from "orval";

export default defineConfig({
	rivalxi: {
		input: {
			target: "http://localhost:8000/openapi.json",
		},

		output: {
			mode: "tags-split",

			target: "../api/rivalxi.ts",

			schemas: "../types/schemas",

			client: "react-query",

			httpClient: "fetch",

			clean: true,

			override: {
				mutator: {
					path: "./api/api-client.ts",
					name: "apiFetch",
				},
			},
		},
	},
});
