from fastapi import FastAPI

app = FastAPI(
    title = "Enterprise AI Agent Platform API"
)

@app.get("/")
def root():
    return {
        "message":"EAAP API Running"
    }