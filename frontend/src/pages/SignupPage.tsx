import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signUpWithCognito, signInWithGoogle } from "../lib/auth";
import { config } from "../lib/config";

const SignupPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);
  const showGoogle = Boolean(config.cognitoOauthDomain);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await signUpWithCognito(email, password);
      if (response.confirmed) {
        navigate("/login", { replace: true });
      } else {
        navigate(`/verify-email?email=${encodeURIComponent(email)}`, { replace: true });
      }
    } catch (err: any) {
      setError(err?.message || "Unable to create account.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setGoogleLoading(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (err: any) {
      setError(err?.message || "Unable to start Google sign in.");
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-brand-navy">Create your account</h1>
        <p className="mt-2 text-sm text-slate-600">
          Get started with Quidme in minutes.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
              required
              disabled={loading}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-brand-sky"
                required
                minLength={6}
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-700"
                aria-label={showPassword ? "Hide password" : "Show password"}
                disabled={loading}
              >
                <span className="text-xs font-semibold">{showPassword ? "Hide" : "Show"}</span>
              </button>
            </div>
          </div>

          {error && <div className="text-sm text-red-500">{error}</div>}

          <button
            type="submit"
            className="w-full rounded-full bg-brand-sky px-4 py-3 text-sm font-semibold text-white"
            disabled={loading}
          >
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>

        {showGoogle && (
          <button
            type="button"
            onClick={handleGoogle}
            className="mt-4 w-full rounded-full border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700"
            disabled={loading || googleLoading}
          >
            {googleLoading ? "Redirecting..." : "Continue with Google"}
          </button>
        )}

        <div className="mt-6 text-center text-sm text-slate-600">
          Already have an account?{" "}
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="text-brand-sky hover:underline"
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
