import QuidmeLogo from "./QuidmeLogo";

const SessionLoader = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="flex flex-col items-center">
        <div className="quidme-loader">
          <div className="quidme-loader__halo" />
          <QuidmeLogo
            alt="Quidme"
            containerClassName="quidme-loader__logo"
            logoClassName="h-[82%] w-[82%]"
            withBadge={false}
          />
          <div className="quidme-loader__sparkle quidme-loader__sparkle--a" />
          <div className="quidme-loader__sparkle quidme-loader__sparkle--b" />
          <div className="quidme-loader__sparkle quidme-loader__sparkle--c" />
        </div>
        <div className="mt-6 flex items-center gap-2">
          <span className="quidme-loader__dot" />
          <span className="quidme-loader__dot quidme-loader__dot--delay-1" />
          <span className="quidme-loader__dot quidme-loader__dot--delay-2" />
        </div>
      </div>
    </div>
  );
};

export default SessionLoader;
