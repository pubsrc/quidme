import { useEffect, useState } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import { signOutWithCognito } from "../lib/auth";
import { useTheme } from "../theme/ThemeProvider";

const SettingsPage = () => {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const [email, setEmail] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteConfirmChecked, setDeleteConfirmChecked] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    const loadEmail = async () => {
      try {
        const session = await fetchAuthSession();
        const tokenEmail = session.tokens?.idToken?.payload?.email;
        setEmail(typeof tokenEmail === "string" ? tokenEmail : "");
      } catch {
        setEmail("");
      }
    };
    loadEmail();
  }, []);

  const openDeleteDialog = () => {
    setDeleteDialogOpen(true);
    setDeleteConfirmChecked(false);
    setDeleteError(null);
  };

  const closeDeleteDialog = () => {
    if (!deleteLoading) {
      setDeleteDialogOpen(false);
      setDeleteConfirmChecked(false);
      setDeleteError(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deleteConfirmChecked) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      await api.deleteAccount();
      await signOutWithCognito();
      window.location.href = "/";
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : t("pages.settings.delete_failed"));
      setDeleteLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 md:space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">{t("pages.settings.title")}</h2>
        <p className="mt-2 text-base text-slate-500 md:text-lg">{t("pages.settings.subtitle")}</p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white md:rounded-3xl">
        <div className="p-4 md:p-6">
          <h3 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">{t("pages.settings.profile")}</h3>

          <div className="mt-6 space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 md:text-lg">{t("pages.settings.email")}</label>
              <input
                type="email"
                value={email}
                disabled
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-slate-300 focus:outline-none md:rounded-2xl md:px-4 md:py-3 md:text-lg"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white md:rounded-3xl">
        <div className="p-4 md:p-6">
          <h3 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">Appearance</h3>
          <p className="mt-2 text-sm text-slate-500 md:text-base">
            Choose between Default, Gold, and Dark themes.
          </p>
          <div className="mt-5 inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1">
            <button
              type="button"
              onClick={() => setTheme("classic")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                theme === "classic" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:bg-white/70"
              }`}
            >
              Default
            </button>
            <button
              type="button"
              onClick={() => setTheme("gold-cute")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                theme === "gold-cute" ? "bg-amber-500 text-white shadow-sm" : "text-slate-600 hover:bg-white/70"
              }`}
            >
              Gold
            </button>
            <button
              type="button"
              onClick={() => setTheme("dark")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                theme === "dark" ? "bg-slate-900 text-white shadow-sm" : "text-slate-600 hover:bg-white/70"
              }`}
            >
              Dark
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-red-400 bg-white p-4 md:rounded-3xl md:p-6">
        <h3 className="text-2xl font-bold tracking-tight md:text-3xl">{t("pages.settings.account_management")}</h3>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-lg font-semibold text-slate-900 md:text-xl">{t("pages.settings.delete_account")}</div>
            <p className="mt-2 text-sm text-slate-500 md:text-base">
              {t("pages.settings.delete_description")}
            </p>
          </div>
          <button
            type="button"
            onClick={openDeleteDialog}
            className="rounded-xl bg-red-500 px-5 py-2 text-sm font-semibold text-white hover:bg-red-600 md:rounded-2xl md:px-7 md:py-3 md:text-lg"
          >
            {t("pages.settings.delete_account")}
          </button>
        </div>
      </div>

      {deleteDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" aria-hidden onClick={closeDeleteDialog} />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
            className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
          >
            <h2 id="delete-dialog-title" className="text-xl font-semibold text-red-800">{t("pages.settings.delete_modal_title")}</h2>
            <p className="mt-3 text-sm text-slate-600">
              {t("pages.settings.delete_modal_intro")}
            </p>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600">
              <li>{t("pages.settings.delete_item_links")}</li>
              <li>{t("pages.settings.delete_item_transactions")}</li>
              <li>{t("pages.settings.delete_item_stripe")}</li>
              <li>{t("pages.settings.delete_item_login")}</li>
            </ul>
            <label className="mt-4 flex items-start gap-3">
              <input
                type="checkbox"
                checked={deleteConfirmChecked}
                onChange={(e) => setDeleteConfirmChecked(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-300 text-red-600 focus:ring-red-500"
              />
              <span className="text-sm text-slate-700">{t("pages.settings.delete_confirm")}</span>
            </label>
            {deleteError && (
              <p className="mt-3 text-sm text-red-600" role="alert">
                {deleteError}
              </p>
            )}
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={closeDeleteDialog}
                disabled={deleteLoading}
                className="rounded-full border border-slate-300 bg-white px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                {t("pages.settings.cancel")}
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={!deleteConfirmChecked || deleteLoading}
                className="rounded-full bg-red-600 px-5 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleteLoading ? t("pages.settings.deleting") : t("pages.settings.delete_my_account")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
