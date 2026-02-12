export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL as string,
  cognitoUserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID as string,
  cognitoClientId: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID as string,
  cognitoRegion: import.meta.env.VITE_COGNITO_REGION as string,
  cognitoOauthDomain: import.meta.env.VITE_COGNITO_OAUTH_DOMAIN as string,
  oauthRedirectSignIn: import.meta.env.VITE_OAUTH_REDIRECT_SIGN_IN as string,
  oauthRedirectSignOut: import.meta.env.VITE_OAUTH_REDIRECT_SIGN_OUT as string,
};

export const assertConfig = () => {
  const requiredKeys = [
    "apiBaseUrl",
    "cognitoUserPoolId",
    "cognitoClientId",
    "cognitoRegion",
    "oauthRedirectSignIn",
    "oauthRedirectSignOut",
  ] as const;

  const missing = requiredKeys.filter((key) => !config[key]);

  if (missing.length > 0) {
    throw new Error(`Missing env vars: ${missing.join(", ")}`);
  }
};
