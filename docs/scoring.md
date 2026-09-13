# How your Health Score is calculated

Scoring version: **2026.1** (see `apps/api/config/scoring.yaml`, the single
source of truth this document explains — if the two ever disagree, the
YAML file is correct and this file is out of date).

This document exists so you never have to take a score on faith. Every
number the Audit Engine shows you is either counted directly from your own
profile data, or judged by AI against a fixed, published rubric — never a
black box.

## The big picture

Your **overall Health Score** is a weighted average of five category
scores:

| Category | Weight |
| --- | --- |
| Profile | 30% |
| Visibility | 20% |
| Engagement | 20% |
| Content | 15% |
| Career | 15% |

Each category score is, in turn, a weighted average of a handful of
**components** — the tables below list every one.

## What happens when we don't have enough data

We never guess, and we never penalize you for a gap that isn't your
fault (like a field the LinkedIn API doesn't expose, or a hub you
haven't used yet). If a component can't be computed — a target role was
never given, a resume hasn't been uploaded, you haven't connected
LinkedIn or entered your network numbers — it's simply **left out**, and
the remaining components' weights are scaled up proportionally so they
still add to 100%. The same rule applies one level up: if an entire
category can't be scored (or its category audit failed unexpectedly),
its weight is dropped from the overall score instead of counting as a
zero.

Concretely: if Profile's `skills_coverage` (weight 15) is unavailable
because you haven't told us a target role, your Profile score is the
weighted average of the other four components, re-weighted to sum to
100 — not "15 points short."

Everywhere this happens, the audit tells you *why*: each category result
carries an `inputs_available` map and, often, a specific finding with an
`unlock` message explaining exactly what would turn the gap into a score.

## Profile — 30%

| Component | Weight | What it measures |
| --- | --- | --- |
| Completeness | 25% | Reuses the Profile Hub's completeness score: whether your headline, About, experience, skills, and certifications/projects are present and substantial. |
| Headline quality | 20% | AI judges whether your headline is specific, states a value proposition, and carries role-relevant keywords — never just a job title. |
| About quality | 20% | AI judges whether your About section has a hook, real substance, a clear structure, and a call to action. |
| Experience quality | 20% | AI judges whether your experience bullets read as quantified achievements rather than plain duty statements. |
| Skills coverage | 15% | The share of your target role's commonly-expected skills that appear in your own skills list. |

The three "quality" components come from a single AI call that grades all
three sections at once against a fixed rubric — it only ever comments on
text you've actually written; it never invents credentials or experience
you don't have.

## Content — 15%

| Component | Weight | What it measures |
| --- | --- | --- |
| Posting readiness | 60% | Whether you've supplied enough recent post history for us to judge posting consistency. There's no LinkedIn post-history import yet, so this is scored only once you paste or upload some of your own posts — until then it's skipped, not penalized. |
| Content opportunities | 40% | How many concrete post ideas your own listed skills and experience suggest, whether or not you've ever posted. |

## Engagement — 20%

| Component | Weight | What it measures |
| --- | --- | --- |
| Network signals | 30% | Your connection count, follower count, and recommendations received — whenever the connected LinkedIn API or your own manual entry makes them visible. |
| Contactability | 30% | Whether your profile invites contact: a custom URL claimed, and an About section that closes with a way to reach you. |
| Engagement opportunities | 40% | Concrete, manual networking ideas suggested by your industry and target role — commenting on specific kinds of posts, joining a relevant group, and so on. Never automation: LinkSavvy will never like, comment, connect, or message on your behalf. |

## Career — 15%

| Component | Weight | What it measures |
| --- | --- | --- |
| Resume presence | 30% | Whether a resume has been uploaded for cross-referencing. There's no resume upload path yet, so this component is always skipped for now — it will start counting once the Career Hub ships it. |
| Role alignment | 50% | The overlap between your listed skills and the skills your target role typically expects. AI generates the expected-skills list once per audit run; the overlap itself is a plain, deterministic count. |
| Readiness gaps | 20% | The specific, named skills your target role expects that don't yet appear on your profile. |

Career can never reach a fully "complete" status today, since resume
presence always contributes nothing — that's expected, not a bug, until
the Career Hub adds resume upload.

## Visibility — 20%

| Component | Weight | What it measures |
| --- | --- | --- |
| Keyword density | 30% | How many of your target role's expected vocabulary words show up across your headline and About section. |
| Custom URL | 15% | Whether you've claimed a custom, memorable LinkedIn URL. |
| Profile metadata | 20% | Whether your industry and location are set — both are fields recruiters filter search by. |
| Skill alignment | 20% | The overlap between your listed skills and your target role's expected skill vocabulary. |
| Brand consistency | 15% | Whether your headline *and* your About section each carry at least one of your target role's expected terms — a simple, deterministic proxy for "these two sections are telling a consistent professional story," rather than an AI judgement call. |

## Where recommendations come from

Every finding an audit raises is looked up in a fixed table
(`apps/api/app/audit/recommendations.py`) that maps it to a concrete
action, a destination in the app, and an estimated impact in points —
never generated freeform by AI. Recommendations are ranked by finding
severity (critical, then important, then opportunity) and, within a tier,
by estimated impact, so the top of your recommendations list is always
the highest-leverage thing you can do next.

Not every finding produces a recommendation card: purely informational
"we don't have enough data yet" findings (like "tell us your target
role") show up in the relevant category's own detail instead of cluttering
your top recommendations with several near-duplicate prompts to fill in
the same missing field.

## Score history

Every completed audit that produces an overall score adds one row to your
90-day score history, tagged with the scoring version that produced it.
If we ever change these weights or add a component, we bump
`scoring_version` — so a jump in your trend line always has an honest
explanation (a real change in your profile, or a change in how we score)
rather than silently comparing scores computed two different ways.

# The Growth Hub's four scores

The Growth Hub (`apps/api/app/growth/`) shows four scores side by side.
One of them — Health — is the same Audit Engine score documented above,
just reshaped for this view. The other three (Visibility, Consistency,
Personal Branding) are new for the Growth Hub and live in their own
`growth:` section of `config/scoring.yaml`, versioned independently as
`growth.scoring_version` (currently also `2026.1`, but the two versions
are free to diverge if one side changes without the other).

Every score — all four — returns the same envelope:

```json
{
  "score_type": "visibility",
  "value": 62,
  "status": "partial",
  "components": [
    {"name": "keyword_coverage", "weight": 25, "value": 80, "evidence": {"...": "..."}}
  ],
  "computed_at": "2026-09-13T12:00:00Z",
  "scoring_version": "2026.1",
  "needed": null
}
```

`status` is one of:

- **ok** — every component was computable.
- **partial** — at least one component is missing (a field the user
  hasn't filled in, a component the AI couldn't support with evidence),
  but there's enough to show a number.
- **insufficient_data** — there isn't enough history yet to compute the
  score meaningfully at all (currently only Consistency, before four
  weeks of posting activity). `needed` explains exactly what's missing —
  never a bare zero.
- **skipped** — nothing has been provided to compute the score from at
  all (no profile snapshot committed, no audit ever run).

A component with `value` set always has non-empty `evidence` — a
component the code (or the AI) couldn't actually support is left out of
`components` entirely rather than shown with a fabricated or blank
justification. This is enforced in code, not just by convention: every
Growth Hub score test asserts it.

## Health — reused, not recomputed

The Growth Hub's Health Score is the exact same overall Health Score
computed above, read back from your existing `score_history` row and
reshaped into the shared envelope — the five categories above become
five components (weight = each category's `category_weights` entry from
`config/scoring.yaml`), and `computed_at`/`scoring_version` come directly
from that row. It is never recomputed here; run an audit to refresh it.
If you've never run an audit, this score is `skipped`.

## Visibility — 25/10/15/15/15/20

| Component | Weight | What it measures |
| --- | --- | --- |
| Keyword coverage | 25% | How many of the target role's vocabulary words appear across the headline, About, *and* experience bullets combined — broader than the Audit Engine's own `keyword_density`, which only looks at headline + About. Uses the same AI-resolved role vocabulary the audit uses (cached, so this costs no extra AI calls after the first). |
| Custom URL | 10% | Whether a custom, memorable LinkedIn URL is claimed. |
| Profile metadata | 15% | Whether industry and location are set — both are fields recruiters filter search by. |
| Skill alignment | 15% | Overlap between the user's listed skills and the target role's expected skill vocabulary. |
| Photo and banner | 15% | Whether a profile photo is set. **Photo-only for now** — `ProfileSnapshot` doesn't capture a banner/background image anywhere yet (see ADR 0009), so this component is disclosed as photo-only rather than silently scored as if banner presence were checked. |
| Recommendations received | 20% | Whether the profile shows received recommendations, scaled against a realistic target of 3. |

Deterministic apart from the keyword-relevance judgement (which role
vocabulary counts as "relevant" is an AI call, same as the audit's).
`skipped` if no profile snapshot has ever been committed.

## Consistency — 30/25/25/20

| Component | Weight | What it measures |
| --- | --- | --- |
| Posts per week | 30% | Average recorded posts per week over the trailing 12 weeks, scored against a target cadence of 2/week. |
| Variance | 25% | How evenly spread posting is across the 12 weeks — a steady weekly habit scores higher than the same total posts bunched into a couple of weeks. |
| Longest gap | 25% | The longest run of consecutive weeks with zero recorded posts. |
| Streak length | 20% | The current run of consecutive weeks with at least one recorded post, scaled against a target streak of 8 weeks. |

Fully deterministic — no AI call at all. Reuses the same 12-week posted-
post window (`app.content.calendar_service.consistency_strip`) the
Content Hub's own consistency strip already computes, so the two never
disagree. If fewer than four of the trailing twelve weeks have any
recorded posting activity, the score is `insufficient_data` rather than a
misleadingly low number — `needed` names how many weeks you have and how
many you need.

## Personal Branding — 25/20/20/20/15

| Component | Weight | What it measures |
| --- | --- | --- |
| Positioning clarity | 25% | Whether a reader could state, in one sentence, who this person is and what they do. |
| Message consistency | 20% | Whether the headline, About, and experience sections tell the same professional story rather than pulling in different directions. |
| Distinctiveness | 20% | Whether the profile says something specific to this person, rather than reading like it could describe anyone in the role. |
| Proof | 20% | Whether claims are backed by concrete evidence — a result, a project, a number — rather than unsupported adjectives. |
| Content-to-profile alignment | 15% | Whether the themes of the user's own recent content samples (if any) match the positioning claimed in the profile. If no content samples have been recorded, the AI is told so explicitly and scores this component on that absence rather than guessing. |

This one leans entirely on the gateway: a single AI call
(`growth.personal_branding.v1`) scores all five components at once
against a fixed rubric, and every component in its response must carry
non-empty `evidence` quoting or paraphrasing the user's own text. Any
component the model returns with blank or whitespace-only evidence is
**discarded**, not trusted at face value — the same "no evidence, no
score" rule the audit's own quality judgements follow. If every component
comes back without usable evidence, the whole score is `skipped` rather
than shown as a hollow number; `skipped` also applies if no profile
snapshot has ever been committed.
