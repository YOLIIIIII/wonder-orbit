export class ApiError extends Error {
  constructor(
    message: string,
    public runId?: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  key?: string,
): Promise<T> {
  const response = await fetch("/api" + path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(key ? { "Idempotency-Key": key } : {}),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "服务暂时不可用" }));
    const detail = data.detail;
    throw new ApiError(
      typeof detail === "string"
        ? detail
        : detail?.message || JSON.stringify(detail),
      detail?.run_id,
    );
  }
  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}
