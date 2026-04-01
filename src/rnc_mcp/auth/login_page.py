"""Login page HTML for the OAuth2 authorization flow."""


def render_login_page(
    txn_id: str = "",
    error: str = "",
    show_form: bool = True,
) -> str:
    error_html = ""
    if error:
        error_html = (
            f'<div class="error">{error}</div>'
        )

    form_html = ""
    if show_form:
        form_html = f"""
        <form method="POST" action="/login?txn={txn_id}">
            <label for="rnc_token">RNC API Token</label>
            <input
                type="password"
                id="rnc_token"
                name="rnc_token"
                placeholder="Paste your token here"
                autocomplete="off"
                required
            />
            <p class="hint">
                Get your token at
                <a href="https://ruscorpora.ru/accounts/profile/for-devs"
                   target="_blank"
                   rel="noopener">
                    ruscorpora.ru/accounts/profile/for-devs
                </a>
            </p>
            <button type="submit">Authorize</button>
        </form>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport"
          content="width=device-width, initial-scale=1" />
    <title>Russian National Corpus — Authorization</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont,
                "Segoe UI", Roboto, Helvetica, Arial,
                sans-serif;
            background: #f5f5f5;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1rem;
        }}
        .card {{
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
            padding: 2.5rem;
            width: 100%;
            max-width: 420px;
        }}
        h1 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}
        .subtitle {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }}
        label {{
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.375rem;
        }}
        input[type="password"] {{
            width: 100%;
            padding: 0.625rem 0.75rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 0.9rem;
            transition: border-color 0.15s;
        }}
        input[type="password"]:focus {{
            outline: none;
            border-color: #4a90d9;
            box-shadow: 0 0 0 3px rgba(74, 144, 217, 0.15);
        }}
        .hint {{
            font-size: 0.8rem;
            color: #888;
            margin-top: 0.5rem;
        }}
        .hint a {{
            color: #4a90d9;
            text-decoration: none;
        }}
        .hint a:hover {{
            text-decoration: underline;
        }}
        button {{
            width: 100%;
            margin-top: 1.25rem;
            padding: 0.625rem;
            background: #4a90d9;
            color: #fff;
            border: none;
            border-radius: 6px;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s;
        }}
        button:hover {{
            background: #3a7bc8;
        }}
        .error {{
            background: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
            border-radius: 6px;
            padding: 0.625rem 0.75rem;
            font-size: 0.875rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Russian National Corpus</h1>
        <p class="subtitle">
            Enter your RNC API token to authorize access.
        </p>
        {error_html}
        {form_html}
    </div>
</body>
</html>"""
