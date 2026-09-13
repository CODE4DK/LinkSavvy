/**
 * LinkedIn doesn't publish these numbers -- they're observed values
 * that can and do drift as LinkedIn changes its own rendering. If the
 * composer's preview stops matching what LinkedIn actually shows,
 * these are the constants to re-measure and update.
 */

/** LinkedIn's hard character limit for a text post. */
export const LINKEDIN_POST_CHAR_LIMIT = 3000;

/** Where the character counter switches to a warning colour, ahead of
 * the hard limit so the user notices before they're at the wall. */
export const LINKEDIN_WARNING_THRESHOLD = 2800;

/** Roughly how many characters LinkedIn shows before truncating a post
 * behind a "…see more" control, on desktop. Mobile's cut point is
 * different (and varies by device width); this single approximation
 * is what the preview uses for both, since an exact per-surface figure
 * isn't published and would need its own periodic re-measurement. */
export const LINKEDIN_FOLD_CHAR_LIMIT = 210;
