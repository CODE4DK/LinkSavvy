"""Renders a notification into an email: one responsive HTML layout
matching the app's own design tokens (styles/tokens.css's light-theme
values, inlined -- most mail clients strip <style> blocks or ignore CSS
custom properties, so the palette is hardcoded here rather than shared
via import), plus a plain-text alternative every send includes.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

_COLOR_BG = "#ffffff"
_COLOR_FG = "#111827"
_COLOR_FG_MUTED = "#4b5563"
_COLOR_BORDER = "#e0e3e8"
_COLOR_PRIMARY = "#1d4ed8"
_COLOR_PRIMARY_FG = "#ffffff"


@dataclass(frozen=True, slots=True)
class RenderedEmail:
    subject: str
    html_body: str
    text_body: str


def render_notification_email(
    *,
    title: str,
    body: str,
    action_label: str | None = None,
    action_url: str | None = None,
    unsubscribe_url: str | None = None,
) -> RenderedEmail:
    button_html = ""
    if action_label and action_url:
        button_html = f"""
        <tr>
          <td style="padding: 24px 32px 8px 32px;">
            <a href="{escape(action_url)}"
               style="display:inline-block;background:{_COLOR_PRIMARY};color:{_COLOR_PRIMARY_FG};
                      text-decoration:none;padding:10px 20px;border-radius:6px;font-weight:600;
                      font-family:Arial,Helvetica,sans-serif;font-size:14px;">
              {escape(action_label)}
            </a>
          </td>
        </tr>"""

    unsubscribe_html = ""
    if unsubscribe_url:
        unsubscribe_html = f"""
        <p style="margin:24px 0 0 0;font-size:12px;color:{_COLOR_FG_MUTED};">
          <a href="{escape(unsubscribe_url)}" style="color:{_COLOR_FG_MUTED};">
            Unsubscribe from this type of email
          </a>
        </p>"""

    html_body = f"""<!doctype html>
<html>
  <body style="margin:0;padding:0;background:{_COLOR_BG};font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="max-width:600px;width:100%;margin:0 auto;">
      <tr>
        <td style="padding:32px 32px 0 32px;">
          <p style="margin:0;font-size:13px;letter-spacing:0.05em;color:{_COLOR_PRIMARY};
                    text-transform:uppercase;font-weight:700;">LinkSavvy</p>
          <h1 style="margin:12px 0 0 0;font-size:20px;color:{_COLOR_FG};">{escape(title)}</h1>
        </td>
      </tr>
      <tr>
        <td style="padding:12px 32px 0 32px;">
          <p style="margin:0;font-size:14px;line-height:1.6;color:{_COLOR_FG_MUTED};">
            {escape(body)}
          </p>
        </td>
      </tr>
      {button_html}
      <tr>
        <td style="padding:32px;">
          <hr style="border:none;border-top:1px solid {_COLOR_BORDER};margin:0 0 16px 0;" />
          <p style="margin:0;font-size:12px;color:{_COLOR_FG_MUTED};">
            You're receiving this because of activity on your LinkSavvy account.
          </p>
          {unsubscribe_html}
        </td>
      </tr>
    </table>
  </body>
</html>"""

    text_lines = [title, "", body]
    if action_label and action_url:
        text_lines += ["", f"{action_label}: {action_url}"]
    if unsubscribe_url:
        text_lines += ["", f"Unsubscribe: {unsubscribe_url}"]
    text_body = "\n".join(text_lines)

    return RenderedEmail(subject=title, html_body=html_body, text_body=text_body)
