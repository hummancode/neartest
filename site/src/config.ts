// Site-wide settings. Everything the owner still has to decide lives here.

// Brand name is still a placeholder (see CLAUDE.md).
export const SITE_NAME = "[MARKA]";
export const DISCLAIMER = "Yatırım tavsiyesi değildir.";

// Contact for KVKK requests. Empty = shown as "eklenecek" on the privacy page.
export const CONTACT_EMAIL = "";
// Legal entity / person acting as data controller (veri sorumlusu).
export const DATA_CONTROLLER = "";

// Newsletter: the provider's plain HTML form endpoint (POST, field name "email").
// Empty = signup form is disabled. No third-party script is loaded either way;
// the browser only talks to the provider when the visitor submits the form.
export const NEWSLETTER = {
  provider: "",        // e.g. "Buttondown" — shown on the privacy page
  formAction: "",      // e.g. "https://buttondown.com/api/emails/embed-subscribe/<name>"
};

// Cloudflare Web Analytics (cookie-free). Empty = no analytics script at all.
export const CF_ANALYTICS_TOKEN = "";

// Legal texts are drafts until reviewed by a lawyer; shows a notice while true.
export const LEGAL_DRAFT = true;
