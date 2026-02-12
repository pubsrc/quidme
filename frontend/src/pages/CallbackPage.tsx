import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchAuthSession } from "aws-amplify/auth";

const CallbackPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const finalize = async () => {
      try {
        const session = await fetchAuthSession();
        if (session.tokens?.idToken) {
          navigate("/app/payment-links", { replace: true });
        } else {
          navigate("/login", { replace: true });
        }
      } catch {
        navigate("/login", { replace: true });
      }
    };

    finalize();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-slate-600">Signing you in...</div>
    </div>
  );
};

export default CallbackPage;
