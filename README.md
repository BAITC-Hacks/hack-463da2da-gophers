# hack-463da2da-gophers
Hackathon team repository for Gophers

## OpenAI for jury checks

The recommendation explainer uses OpenAI as its primary provider and NVIDIA as a fallback.
Before starting the project, copy `.env.example` to `.env` and place the API key issued for
the check in `OPENAI_API_KEY`. Docker Compose passes this variable to the backend automatically.

Do not commit `.env` or paste a real key into source code, issues, or chat. The template file is
safe to share; it contains placeholders only. The API key is used server-side, never by the browser.
