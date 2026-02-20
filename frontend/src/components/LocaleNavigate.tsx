import { Navigate, type NavigateProps } from "react-router-dom";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const LocaleNavigate = ({ to, ...props }: NavigateProps) => {
  const { localeTo } = useLocaleNavigate();
  return <Navigate to={localeTo(to)} {...props} />;
};

export default LocaleNavigate;

