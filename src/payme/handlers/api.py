from __future__ import annotations

from mangum import Mangum

from payme.api.main import app

handler = Mangum(app)
