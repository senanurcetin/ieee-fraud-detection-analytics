# Archived Power BI Load Notes

Power BI is no longer the primary reporting surface for this project. These notes are retained only to explain the earlier prototype.

Current presentation layer:

```text
webapp/
https://fraud-project-web.vercel.app
```

The active dashboard connects to BigQuery through the server-side FastAPI API and Vercel environment variables. No local Power BI Desktop setup is required for the final presentation.
