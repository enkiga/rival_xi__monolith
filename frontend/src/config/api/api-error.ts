export class ApiError extends Error {
	public readonly status: number;
	public readonly body?: unknown;

	constructor(status: number, body?: unknown) {
		super(ApiError.getMessage(body, status));

		this.name = "ApiError";
		this.status = status;
		this.body = body;
	}

	private static getMessage(body: unknown, status: number): string {
		if (
			body &&
			typeof body === "object" &&
			"detail" in body &&
			typeof body.detail === "string"
		) {
			return body.detail;
		}

		return `Request failed with status ${status}`;
	}
}
