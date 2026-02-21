import { useEffect } from "react";

type JsonLd = Record<string, unknown> | Array<Record<string, unknown>>;

type UseSeoOptions = {
  title: string;
  description: string;
  keywords?: string[];
  canonicalPath?: string;
  ogType?: string;
  locale?: string;
  imagePath?: string;
  noIndex?: boolean;
  structuredData?: JsonLd;
};

const upsertMetaByName = (name: string, content: string) => {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute("name", name);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
};

const upsertMetaByProperty = (property: string, content: string) => {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[property="${property}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute("property", property);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
};

const upsertCanonical = (href: string) => {
  let el = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", "canonical");
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
};

const upsertJsonLd = (data: JsonLd) => {
  const id = "seo-structured-data";
  let el = document.getElementById(id) as HTMLScriptElement | null;
  if (!el) {
    el = document.createElement("script");
    el.id = id;
    el.type = "application/ld+json";
    document.head.appendChild(el);
  }
  el.text = JSON.stringify(data);
};

export const useSeo = ({
  title,
  description,
  keywords,
  canonicalPath = "/",
  ogType = "website",
  locale = "en_GB",
  imagePath = "/android-chrome-512x512.png",
  noIndex = false,
  structuredData,
}: UseSeoOptions) => {
  useEffect(() => {
    const origin = window.location.origin;
    const canonicalUrl = new URL(canonicalPath, origin).toString();
    const imageUrl = new URL(imagePath, origin).toString();

    document.title = title;
    upsertCanonical(canonicalUrl);

    upsertMetaByName("description", description);
    if (keywords && keywords.length > 0) {
      upsertMetaByName("keywords", keywords.join(", "));
    }
    upsertMetaByName("robots", noIndex ? "noindex, nofollow" : "index, follow");

    upsertMetaByProperty("og:type", ogType);
    upsertMetaByProperty("og:title", title);
    upsertMetaByProperty("og:description", description);
    upsertMetaByProperty("og:url", canonicalUrl);
    upsertMetaByProperty("og:locale", locale);
    upsertMetaByProperty("og:site_name", "Quidme");
    upsertMetaByProperty("og:image", imageUrl);

    upsertMetaByName("twitter:card", "summary_large_image");
    upsertMetaByName("twitter:title", title);
    upsertMetaByName("twitter:description", description);
    upsertMetaByName("twitter:image", imageUrl);

    if (structuredData) {
      upsertJsonLd(structuredData);
    }
  }, [canonicalPath, description, imagePath, keywords, locale, noIndex, ogType, structuredData, title]);
};
