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
