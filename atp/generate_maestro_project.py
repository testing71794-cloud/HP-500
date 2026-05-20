"""
HP 500 Panorama Maestro project generator.

1) Ensures Kodak-style folder layout under repo root.
2) Writes one Maestro flow per SL ATP row: flows/signup-login/SL_XXX.yaml

Prerequisite: python atp/export_atp.py (builds hp500_panorama_atp_cases.json)

Usage:
  python atp/generate_maestro_project.py
  python atp/generate_maestro_project.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

APP_ID = "com.hp.impulse.panorama"
ROOT = Path(__file__).resolve().parents[1]
ATP_JSON = ROOT / "atp" / "hp500_panorama_atp_cases.json"

# Excel "SL" sheet row (1 = header) -> automation spec
SL_SPECS: dict[int, dict] = {
    2: {"kind": "signup_email_alert", "name": "QA SL002", "email": "t", "password": "t"},
    3: {"kind": "signup_password_alert", "name": "QA SL003", "email": "test@test.com", "password": "t"},
    4: {"kind": "signup_password_alert", "name": "QA SL004", "email": "test@test.com", "password": "testpass1"},
    5: {"kind": "signup_password_alert", "name": "QA SL005", "email": "test@test.com", "password": "Testpass"},
    6: {"kind": "signup_success", "name": "QA SL006", "email": "${SL_VALID_EMAIL}", "password": "Testpass1"},
    7: {"kind": "login_email_alert", "name": "QA SL007", "email": "T", "password": "T"},
    8: {"kind": "login_password_alert", "name": "QA SL008", "email": "${SL_VALID_EMAIL}", "password": "Testpass"},
    9: {"kind": "login_password_alert", "name": "QA SL009", "email": "${SL_VALID_EMAIL}", "password": "testpass1"},
    10: {"kind": "login_password_alert", "name": "QA SL010", "email": "${SL_VALID_EMAIL}", "password": "t"},
    11: {"kind": "login_success", "name": "QA SL011", "email": "${SL_VALID_EMAIL}", "password": "Testpass1"},
    12: {"kind": "forgot_send", "email": "${SL_VALID_EMAIL}"},
    13: {"kind": "reset_placeholder", "hint": "First-use reset link from email."},
    14: {"kind": "reset_placeholder", "hint": "Reuse reset link; expect cannot use again."},
    15: {"kind": "reset_placeholder", "hint": "Expired reset link (set SL_RESET_LINK_SL015)."},
    16: {"kind": "reset_password_field", "password": "testpass1", "assert": "upper"},
    17: {"kind": "reset_password_field", "password": "testpass", "assert": "number"},
    18: {"kind": "reset_password_field", "password": "Test1", "assert": "length"},
    19: {"kind": "skip_signup"},
}

STRUCTURE_MARKERS = [
    ROOT / ".maestro" / "screenshots",
    ROOT / "flows" / ".maestro" / "screenshots",
    ROOT / "flows" / "connection" / "subflows",
    ROOT / "flows" / "onboarding" / "subflows",
    ROOT / "flows" / "signup-login" / ".maestro" / "screenshots",
    ROOT / "flows" / "signup-login" / "scripts",
    ROOT / "flows" / "signup-login" / "subflows",
]

# Match hand-tuned SL_002 / SL_003: assert legal copy, then tap primary "Sign up".
SIGNUP_LEGAL_AND_SUBMIT = textwrap.dedent(
    """\
    - assertVisible: "By signing up you agree to our Terms & Conditions and"
    - assertVisible: "Privacy Policy"
    - tapOn: "Sign up"
    - waitForAnimationToEnd
    """
).rstrip()

MSG_EMAIL_INVALID = "Please enter a valid email address"
MSG_PASSWORD_RULE = (
    "Password must be at least 8 characters. At least one lowercase and one uppercase letter"
)

# Do not overwrite hand-maintained flows when regenerating.
SKIP_EXCEL_ROWS: set[int] = {2, 3}

LOGIN_SUBMIT = textwrap.dedent(
    """\
    - hideKeyboard
    - tapOn:
        text: "Login"
        below: "Forgot password"
    """
).rstrip()

DISMISS_ALERT = textwrap.dedent(
    """\
    - tapOn:
        text: "OK"
        optional: true
    - tapOn:
        text: "Ok"
        optional: true
    """
).rstrip()


def ensure_structure() -> None:
    for d in STRUCTURE_MARKERS:
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")


def load_sl_cases() -> list[dict]:
    data = json.loads(ATP_JSON.read_text(encoding="utf-8"))
    return sorted([c for c in data if c.get("sheet") == "SL"], key=lambda c: c["excel_row"])


def tags_for(kind: str, atp_id: str, sl_n: int | None) -> list[str]:
    t = ["hp-panorama", "atp", atp_id]
    if sl_n is not None:
        t.append(f"test-{sl_n}")
    if "signup" in kind:
        t.append("signup")
    elif kind in ("skip_signup",):
        t.append("signup")
    elif kind.startswith("login") or "forgot" in kind or "reset" in kind:
        t.append("login")
    if "success" in kind or kind == "skip_signup":
        t.append("positive")
    elif kind == "reset_placeholder":
        t.append("edge")
    else:
        t.append("negative")
    return t


def build_signup_form(name: str, email: str, password: str) -> str:
    return textwrap.dedent(
        f"""\
        - tapOn: "Full name"
        - inputText: "{name}"
        - tapOn: "Email"
        - inputText: "{email}"
        - tapOn: "Password"
        - inputText: "{password}"
        - hideKeyboard
        """
    ).rstrip()


def build_login_form(email: str, password: str) -> str:
    return textwrap.dedent(
        f"""\
        - tapOn: "Email"
        - inputText: "{email}"
        - tapOn: "Password"
        - inputText: "{password}"
        """
    ).rstrip()


def commands_for_kind(kind: str, spec: dict) -> str:
    if kind == "skip_signup":
        return textwrap.dedent(
            """\
            - runFlow: subflows/reach_signup_from_cold_start.yaml
            - assertVisible: "By signing up you agree to our Terms & Conditions and"
            - assertVisible: "Privacy Policy"
            - scrollUntilVisible:
                element: "I'll do it later"
                direction: DOWN
                timeout: 20000
            - tapOn: "I'll do it later"
            - waitForAnimationToEnd
            - extendedWaitUntil:
                notVisible: "Full name"
                timeout: 25000
            - assertNotVisible: "Full name"
            - assertVisible:
                text: ".*(?i)(welcome|next|continue|connect|skip|onboarding|power|paper|bluetooth).*"
                optional: true
            """
        ).rstrip()

    if kind == "forgot_send":
        email = spec["email"]
        return textwrap.dedent(
            f"""\
            - runFlow: subflows/reach_login_from_cold_start.yaml
            - tapOn: "Forgot password"
            - waitForAnimationToEnd
            - tapOn: "Email"
            - inputText: "{email}"
            - hideKeyboard
            - tapOn:
                text: "Send"
                optional: true
            - waitForAnimationToEnd
            - assertVisible:
                text: ".*(?i)(email|sent|reset|check).*"
                optional: true
            """
        ).rstrip()

    if kind == "reset_placeholder":
        atp = spec["_atp_id"]
        link = f"${{SL_RESET_LINK_{atp}}}"
        hint = spec.get("hint", "")
        return textwrap.dedent(
            f"""\
            # {hint}
            - waitForAnimationToEnd
            - openLink:
                link: {link}
                autoVerify: true
            - waitForAnimationToEnd
            - assertVisible:
                text: ".*(?i)(reset|password|invalid|expired|link|use).*"
                optional: true
            """
        ).rstrip()

    if kind == "reset_password_field":
        atp = spec["_atp_id"]
        link = f"${{SL_RESET_LINK_{atp}}}"
        pwd = spec["password"]
        ak = spec["assert"]
        if ak == "upper":
            msg = "There should be at least one upper case characters"
        elif ak == "number":
            msg = "There should be at least one number"
        else:
            msg = "Password must contain at least 8 characters"
        return textwrap.dedent(
            f"""\
            - waitForAnimationToEnd
            - openLink:
                link: {link}
                autoVerify: true
            - waitForAnimationToEnd
            - tapOn:
                text: "New password"
                optional: true
            - inputText: "{pwd}"
            - tapOn:
                text: "Confirm password"
                optional: true
            - inputText: "{pwd}"
            - hideKeyboard
            - tapOn:
                text: "Save"
                optional: true
            - waitForAnimationToEnd
            - assertVisible:
                text: "{msg}"
            """
        ).rstrip()

    lines: list[str] = [
        "- launchApp:",
        f"    appId: {APP_ID}",
        "    clearState: true",
    ]
    if kind.startswith("signup"):
        lines.append('- runFlow: subflows/reach_signup_from_cold_start.yaml')
        lines.append(build_signup_form(spec["name"], spec["email"], spec["password"]))
        lines.append(SIGNUP_LEGAL_AND_SUBMIT)
    else:
        lines.append('- runFlow: subflows/reach_login_from_cold_start.yaml')
        lines.append(build_login_form(spec["email"], spec["password"]))
        lines.append(LOGIN_SUBMIT)

    if not kind.startswith("signup"):
        lines.append("- waitForAnimationToEnd")

    anchor = '"Sign up"' if kind.startswith("signup") else '"Login"'
    if kind.endswith("_email_alert"):
        lines.extend(
            [
                "- assertVisible:",
                f'    text: "{MSG_EMAIL_INVALID}"',
                DISMISS_ALERT,
                f"- assertVisible: {anchor}",
            ]
        )
    elif kind.endswith("password_alert"):
        lines.extend(
            [
                "- assertVisible:",
                f'    text: "{MSG_PASSWORD_RULE}"',
                DISMISS_ALERT,
                f"- assertVisible: {anchor}",
            ]
        )
    elif kind == "signup_success":
        lines.extend(
            [
                "- assertNotVisible:",
                f'    text: "{MSG_EMAIL_INVALID}"',
                "- assertNotVisible:",
                f'    text: "{MSG_PASSWORD_RULE}"',
                "- extendedWaitUntil:",
                '    notVisible: "Let creativity roll!"',
                "    timeout: 90000",
                "    optional: true",
                "- assertVisible:",
                '    text: ".*(?i)(welcome|next|continue|connect|skip|onboarding|power|paper|bluetooth).*"',
                "    optional: true",
            ]
        )
    elif kind == "login_success":
        lines.extend(
            [
                "- assertNotVisible:",
                f'    text: "{MSG_EMAIL_INVALID}"',
                "- assertNotVisible:",
                f'    text: "{MSG_PASSWORD_RULE}"',
                "- extendedWaitUntil:",
                '    notVisible: "Forgot password"',
                "    timeout: 90000",
                "    optional: true",
                "- assertVisible:",
                '    text: ".*(?i)(welcome|next|continue|connect|skip|onboarding|power|paper|bluetooth).*"',
                "    optional: true",
            ]
        )

    return "\n".join(lines)


def generate_sl_flow(case: dict, spec: dict) -> str:
    row = case["excel_row"]
    atp_id = case["atp_id"]
    desc = (case.get("test_data") or "").replace('"', "'")
    sl_n = case.get("sl_test_number")
    kind = spec["kind"]

    comments = [
        f"# ATP ID: {atp_id}",
        f"# Description: {desc}",
        f"# Excel SL row: {row}",
    ]
    if sl_n is not None:
        comments.append(f"# sl_test_number: {sl_n}")

    name_line = f"{atp_id} - {desc[:72]}" if desc else atp_id
    tag_list = tags_for(kind, atp_id, sl_n)

    needs_valid_email = "${SL_VALID_EMAIL}" in json.dumps(spec)
    spec = {**spec, "_atp_id": atp_id}
    cmd = commands_for_kind(kind, spec)

    parts: list[str] = ["\n".join(comments), "", f"appId: {APP_ID}"]

    if needs_valid_email:
        parts.extend(["env:", '  SL_VALID_EMAIL: "qa.hp500.sl.valid@hpqa.test"', ""])

    if kind in ("reset_placeholder", "reset_password_field"):
        parts.extend(
            [
                "env:",
                f'  SL_RESET_LINK_{atp_id}: "https://example.com/reset-token-{atp_id}"',
                "",
            ]
        )

    parts.append(f'name: "{name_line}"')
    parts.append("tags:")
    for t in tag_list:
        parts.append(f"  - {t}")
    parts.append("---")

    if kind in ("skip_signup", "forgot_send", "reset_placeholder", "reset_password_field"):
        parts.append("- launchApp:")
        parts.append(f"    appId: {APP_ID}")
        parts.append("    clearState: true")

    parts.append(cmd)

    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not ATP_JSON.exists():
        raise SystemExit(f"Missing {ATP_JSON}; run export_atp.py first.")

    ensure_structure()
    out_dir = ROOT / "flows" / "signup-login"
    cases = load_sl_cases()

    planned: list[tuple[Path, str]] = []
    for case in cases:
        row = case["excel_row"]
        atp_id = case["atp_id"]
        spec = SL_SPECS.get(row)
        if not spec:
            continue
        if row in SKIP_EXCEL_ROWS:
            continue
        planned.append((out_dir / f"{atp_id}.yaml", generate_sl_flow(case, spec)))

    if args.dry_run:
        print(f"Would write {len(planned)} flows (skipping hand-tuned rows {sorted(SKIP_EXCEL_ROWS)})")
        for p, _ in planned:
            print(" ", p)
        return

    for path, content in planned:
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {len(planned)} SL flows to {out_dir}")


if __name__ == "__main__":
    main()
