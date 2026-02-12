import { Amplify } from "aws-amplify";
import {
  signIn as amplifySignIn,
  signUp as amplifySignUp,
  confirmSignUp,
  resendSignUpCode,
  signOut,
  resetPassword,
  confirmResetPassword,
  fetchAuthSession,
  signInWithRedirect
} from "aws-amplify/auth";
import { config } from "./config";

export const configureCognito = () => {
  const userPoolId = config.cognitoUserPoolId;
  const userPoolClientId = config.cognitoClientId;
  const region = config.cognitoRegion;

  if (!userPoolId || !userPoolClientId || !region) {
    console.warn("Cognito configuration is missing. Check VITE_COGNITO_* env variables.");
    return;
  }

  const cognitoConfig: any = {
    userPoolId,
    userPoolClientId,
    loginWith: {
      email: true,
    },
  };

  if (config.cognitoOauthDomain) {
    cognitoConfig.loginWith.oauth = {
      domain: config.cognitoOauthDomain,
      scopes: ["openid", "email", "profile"],
      redirectSignIn: [config.oauthRedirectSignIn],
      redirectSignOut: [config.oauthRedirectSignOut],
      identityProvider: "Google",
      responseType: "code",
    };
  }

  Amplify.configure({
    Auth: {
      Cognito: cognitoConfig,
    },
  });
};

export const getIdToken = async (): Promise<string | null> => {
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() ?? null;
  } catch {
    return null;
  }
};

export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getIdToken();
  return !!token;
};

export const signUpWithCognito = async (email: string, password: string) => {
  try {
    const { userId, nextStep } = await amplifySignUp({
      username: email,
      password,
      options: {
        userAttributes: { email },
        autoSignIn: { enabled: false },
      },
    });

    return {
      email,
      userId: userId ?? "",
      confirmed: nextStep.signUpStep !== "CONFIRM_SIGN_UP",
      nextStep,
    };
  } catch (error: any) {
    if (error?.name === "UsernameExistsException") {
      throw new Error("An account with this email already exists.");
    }
    if (error?.name === "InvalidPasswordException") {
      throw new Error("Password does not meet requirements.");
    }
    if (error?.name === "InvalidParameterException") {
      throw new Error("Invalid email or password format.");
    }
    throw new Error(error?.message || "Sign up failed. Please try again.");
  }
};

export const confirmSignUpWithCognito = async (email: string, code: string) => {
  try {
    await confirmSignUp({ username: email, confirmationCode: code });
  } catch (error: any) {
    if (error?.name === "CodeMismatchException") {
      throw new Error("Invalid verification code.");
    }
    if (error?.name === "ExpiredCodeException") {
      throw new Error("Verification code has expired. Please request a new one.");
    }
    if (error?.name === "NotAuthorizedException") {
      throw new Error("This account is already confirmed.");
    }
    throw new Error(error?.message || "Confirmation failed. Please try again.");
  }
};

export const resendConfirmationCode = async (email: string) => {
  try {
    await resendSignUpCode({ username: email });
  } catch (error: any) {
    throw new Error(error?.message || "Failed to resend confirmation code.");
  }
};

export const signInWithCognito = async (email: string, password: string) => {
  try {
    const { isSignedIn, nextStep } = await amplifySignIn({
      username: email,
      password,
    });

    if (!isSignedIn) {
      if (nextStep.signInStep === "CONFIRM_SIGN_UP") {
        const error = new Error("Please verify your email address before signing in.");
        (error as any).code = "USER_NOT_CONFIRMED";
        throw error;
      }
      throw new Error("Sign in incomplete. Please try again.");
    }
  } catch (error: any) {
    if (error?.name === "UserNotFoundException") {
      throw new Error("No account found with this email address.");
    }
    if (error?.name === "NotAuthorizedException") {
      throw new Error("Incorrect email or password.");
    }
    if (error?.name === "UserNotConfirmedException") {
      const err = new Error("Please verify your email address before signing in.");
      (err as any).code = "USER_NOT_CONFIRMED";
      throw err;
    }
    if (error?.name === "TooManyRequestsException") {
      throw new Error("Too many attempts. Please try again later.");
    }
    throw new Error(error?.message || "Sign in failed. Please try again.");
  }
};

export const signOutWithCognito = async () => {
  try {
    await signOut();
  } catch (error: any) {
    throw new Error(error?.message || "Sign out failed.");
  }
};

export const requestPasswordReset = async (email: string) => {
  try {
    await resetPassword({ username: email });
  } catch (error: any) {
    if (error?.name === "UserNotFoundException") {
      throw new Error("No account found with this email address.");
    }
    if (error?.name === "InvalidParameterException") {
      throw new Error("Invalid email format.");
    }
    if (error?.name === "TooManyRequestsException") {
      throw new Error("Too many requests. Please try again later.");
    }
    if (error?.name === "LimitExceededException") {
      throw new Error("Attempt limit exceeded. Please try again later.");
    }
    throw new Error(error?.message || "Failed to send password reset code. Please try again.");
  }
};

export const confirmPasswordReset = async (email: string, code: string, newPassword: string) => {
  try {
    await confirmResetPassword({ username: email, confirmationCode: code, newPassword });
  } catch (error: any) {
    if (error?.name === "CodeMismatchException") {
      throw new Error("Invalid verification code. Please check and try again.");
    }
    if (error?.name === "ExpiredCodeException") {
      throw new Error("Verification code has expired. Please request a new one.");
    }
    if (error?.name === "InvalidPasswordException") {
      throw new Error("Password does not meet requirements.");
    }
    if (error?.name === "InvalidParameterException") {
      throw new Error("Invalid code or password format.");
    }
    if (error?.name === "LimitExceededException") {
      throw new Error("Attempt limit exceeded. Please try again later.");
    }
    throw new Error(error?.message || "Failed to reset password. Please try again.");
  }
};

export const signInWithGoogle = async () => {
  try {
    await signInWithRedirect({ provider: "Google" });
  } catch (error: any) {
    throw new Error(error?.message || "Failed to initiate Google sign-in.");
  }
};
