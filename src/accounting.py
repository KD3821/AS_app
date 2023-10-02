import uvicorn
from fastapi import FastAPI

from settings import accounting_settings
from api import router


app = FastAPI(
    title="Accounting Service For Start-Ups",
    description="Register a Start-Up. Get easy loan. Network, Grow & Enjoy!",
    version="1.0.1"
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "accounting:app",
        host=accounting_settings.server_host,
        port=accounting_settings.server_port,
        reload=True
    )
