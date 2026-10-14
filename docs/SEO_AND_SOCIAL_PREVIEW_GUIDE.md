# SEO, social previews and verified screenshot policy

Public pages have route-specific canonical, title, description, Open Graph/Twitter image and JSON-LD WebPage metadata. The social images below are cropped from actual deployed app screenshots, with source hashes verified against existing 14 October 2026 screenshot manifests. The images are not model-performance evidence.

| Public URL | Social JPEG | Verified source PNG | Source SHA-256 | File size |
| --- | --- | --- | --- | ---: |
| https://fraud-project-web.vercel.app/ | /static/seo/fraud-social.jpg | docs/assets/web_dashboard_executive_overview.png | 6a91f96c3252c6774bec05b8cf27862ccd3b81bf7822fa6c6c4c2596bec2f1a4 | 90494 B |

## Interpretation and maintenance

- Fraud Analytics displays historical governed BigQuery reports, not continuously observed transactions.
- Smart Factory and Visual QC operator dashboards are simulations, not actual equipment feeds.
- A model benchmark screenshot must not be interpreted as a deployment or plant-performance result.
- Cropping and JPEG compression are image-delivery changes; no metrics or visual content were invented.
- Robots/sitemap endpoints advertise public page URLs only. Robots policy is not API authorization.
- External search indexing and social card cache refresh times are controlled by third-party crawlers.
- Regenerate preview assets only from provenance-verified screenshots and re-run the local validation script.

## Verification

Run: python scripts/check_seo_assets.py
Then verify public URLs plus /robots.txt and /sitemap.xml after release.
