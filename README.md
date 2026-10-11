# radanya.com

English personal hub for Daniil Pak. The site is generated from versioned JSON data and deploys as a dependency-free static site.

## Build and validate

```bash
python3 build.py
python3 scripts/validate.py
python3 -m http.server 8080 --directory dist
```

Content lives in `content/`. Only `published` projects with `publicPermission: true` can reach `dist/`. External integrations are configured in `content/integrations.json`; disabled integrations fall back to branded email links.

## Publishing

GitHub Actions builds and validates the allowlisted public tree before deploying Pages. Preserve existing MX, SPF, DKIM and DMARC records when attaching `radanya.com`.

