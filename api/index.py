"""The Concierge API as a Vercel Python function. deploy/api/vercel.json sends every path here.

Railway, where the API used to run, is gone, so it now runs on Vercel's free plan as the project
zomato-concierge-api, deployed with scripts/deploy-api.sh. The page's Vercel project proxies
/api/* and /health to it (frontend/vercel.json).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.main import app  # noqa: E402,F401
