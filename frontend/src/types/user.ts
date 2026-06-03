/** Matches backend `UserResponse`. */
export interface UserResponse {
  id: string;
  username: string;
  email: string;
  preferences: Record<string, unknown> | null;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
}

/** Matches backend `TokenResponse`. */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}
