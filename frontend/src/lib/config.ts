const DEFAULT_API_BASE_URL = "http://localhost:8200/api/v1";

/** REST API base URL (trailing path included). Set via `VITE_API_BASE_URL` in `.env`. */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;
