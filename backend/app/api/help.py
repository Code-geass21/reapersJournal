from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/help", tags=["Help"])

class HelpArticle(BaseModel):
    slug: str
    title: str
    content: str

# Expanded markdown help articles
ARTICLES = {
    "getting-started": {
        "title": "Getting Started",
        "content": "### Welcome to Reaper's Journal\n\nTo start logging trades:\n\n1. **Add Instruments:** Go to **Settings > Instruments** and add the currency pairs you trade. *Note: You must know the TwelveData API symbol (e.g., `USDJPY`).*\n2. **Create a Strategy:** Go to **Strategies** and click `+ New Strategy`. Define your rules and constraints here.\n3. **Log a Trade:** Head to the **Journal** and click `+ New Trade`."
    },
    "strategy-rules": {
        "title": "Strategy Rules & Constraints",
        "content": "### How Rules Work\nRules enforce discipline. When you log a trade, the system generates a checklist based on your strategy's rules.\n\n* **Entry/Exit Rules**: Manual checklist items you must tick off before entering a trade.\n* **Risk Rules**: Automated parameters (like Max Lot Size or Minimum R-Multiple). The system will automatically flag your trade with a warning if you violate these.\n\n*Note: Editing a trade or a strategy rule will automatically re-evaluate all open trades to check for new violations.*"
    },
    "partial-exits": {
        "title": "Scaling Out (Partial Exits)",
        "content": "### Logging Partial Exits\nWhen you scale out of a winning position:\n1. Click on the open trade in your Journal.\n2. Click **Log Exit / Scale Out**.\n3. Enter the exit price and the specific **Size to Close** (e.g., closing 0.5 lots out of a 1.0 lot position).\n\nThe system automatically calculates the realized P&L for that specific chunk, deducts the size from your open position, and updates your weighted R-Multiple. Once the size hits 0, the trade automatically moves to `Closed`."
    },
    "backup-restore": {
        "title": "Data Portability & Backups",
        "content": "### Your Data is Yours\nGo to **Settings > Backup/Export** to download your entire journal as a `.zip` file. This includes all your raw JSON data and your uploaded screenshots.\n\n### Restoring Data\nIf you move to a new server, you can upload this `.zip` file in the **Restore Data** tab. \n\n⚠️ **WARNING:** Restoring a backup completely overwrites your current journal. The system will safely remap your IDs, but you must enter your password to confirm."
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
