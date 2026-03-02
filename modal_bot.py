import modal
import os
import subprocess

# Define the Modal Image with necessary dependencies
# Note: python-telegram-bot requires nest_asyncio logic handling or specific loop setups for Modal
image = (
    modal.Image.debian_slim()
    .pip_install(
        "python-telegram-bot",
        "requests",
        "python-dotenv",
        "nest_asyncio",
        "pandas",
        "numpy"
    )
)

app = modal.App("poly-granted-scout-v3")

# We use a Secret to store the Telegram Token
# You must create this secret in your Modal dashboard or via CLI
# modal secret create telegram-secrets TELEGRAM_TOKEN=your_token

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("telegram-secrets")],
    timeout=86400, # Max timeout for a single run
)
def run_bot():
    from bot import main
    print("🚀 Starting PolyGranted Scout on Modal Cloud...")
    main()

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("telegram-secrets")],
    schedule=modal.Period(minutes=15), # Backup scheduler if polling fails
)
def background_check():
    from bot import run_scout_scan
    # This can be used for persistent background tasks if needed
    pass

if __name__ == "__main__":
    # To deploy: modal deploy modal_bot.py
    run_bot.remote()
