import { VITE_API_URL } from "../env";
import { ApiError } from "./api-error";

const API_URL = VITE_API_URL;

export async function apiFetch<T>(
	url: string,
	options: RequestInit,
): Promise<T> {
	const requestUrl = url.startsWith("http") ? url : `${API_URL}${url}`;

	const response = await fetch(requestUrl, {
		...options,

		// Required when using cookie/session authentication.
		credentials: "include",

		headers: {
			...options.headers,
		},
	});

	if (!response.ok) {
		let body: unknown;

		try {
			body = await response.json();
		} catch {
			body = undefined;
		}

		throw new ApiError(response.status, body);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	const contentType = response.headers.get("content-type");

	if (contentType?.includes("application/json")) {
		return response.json() as Promise<T>;
	}

	return response.text() as Promise<T>;
}
