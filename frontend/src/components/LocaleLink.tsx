import { Link, type LinkProps } from "react-router-dom";
import { useLocaleNavigate } from "../lib/useLocaleNavigate";

const LocaleLink = ({ to, ...props }: LinkProps) => {
  const { localeTo } = useLocaleNavigate();
  return <Link to={localeTo(to)} {...props} />;
};

export default LocaleLink;

