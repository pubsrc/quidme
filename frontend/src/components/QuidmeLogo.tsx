type QuidmeLogoProps = {
  alt: string;
  containerClassName?: string;
  logoClassName?: string;
  withBadge?: boolean;
};

const joinClasses = (...values: Array<string | undefined>) => values.filter(Boolean).join(" ");

const QuidmeLogo = ({ alt, containerClassName, logoClassName, withBadge = true }: QuidmeLogoProps) => {
  return (
    <div className={joinClasses(withBadge ? "quidme-logo-badge" : undefined, containerClassName)}>
      <img src="/quidme-logo.svg" alt={alt} className={logoClassName} />
    </div>
  );
};

export default QuidmeLogo;
