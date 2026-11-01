from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/help", tags=["Help"])

class HelpArticle(BaseModel):
    slug: str
    title: str
    content: str

# Hardcoded markdown content for Phase 1
ARTICLES = {
    "getting-started": {
        "title": "Getting Started",
        "content": "### Welcome to Reaper's Journal\n\nTo start logging trades:\n1. Go to **Settings** and add your instruments.\n2. Create a **Strategy** with specific rules.\n3. Head to the **Journal** to log your first trade."
    },
    "strategy-rules": {
        "title": "Strategy Rules & Constraints",
        "content": "### How Rules Work\nRules enforce discipline. When you log a trade, the system generates a checklist based on your strategy's rules.\n\n* **Entry Rules**: Setup conditions.\n* **Risk Rules**: Sizing and stop-loss limits.\n* **Filters**: Time of day or news avoidance."
    },
    "backup-restore": {
        "title": "Backup & Restore",
        "content": "### Your Data is Yours\nGo to **Settings > Backup** to download your entire journal as a JSON + ZIP archive. To restore, upload the ZIP in the Restore tab and provide your password."
    }
}

@router.get("/", response_model=List[dict])
def list_articles():
    """Returns a lightweight list of available articles for the sidebar."""
    return [{"slug": k, "title": v["title"]} for k, v in ARTICLES.items()]

@router.get("/{slug}", response_model=HelpArticle)
def get_article(slug: str):
    """Fetches the full markdown content of a specific article."""
    if slug not in ARTICLES:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"slug": slug, **ARTICLES[slug]}
