import uvicorn

if __name__ == "__main__":
    print("Starting PrepSense Assessment API on http://0.0.0.0:8000...")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)

