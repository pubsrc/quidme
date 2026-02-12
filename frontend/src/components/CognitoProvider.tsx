import { useEffect } from "react";
import { configureCognito } from "../lib/auth";

const CognitoProvider = ({ children }: { children: React.ReactNode }) => {
  useEffect(() => {
    configureCognito();
  }, []);

  return <>{children}</>;
};

export default CognitoProvider;
