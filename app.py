import asyncio
import json
import websockets
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import os

WS_URL = "wss://stream.plsdonate.com/api/user/5826911946/websocket"
donation_totals = {}

app = FastAPI()

# Allow frontend JS to fetch API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve frontend
@app.get("/")
def get_index():
    return FileResponse("static/index.html")

# API endpoint returning top donors
@app.get("/leaderboard")
def get_leaderboard():
    sorted_donors = sorted(donation_totals.items(), key=lambda x: x[1], reverse=True)
    return [{"username": u, "amount": a} for u, a in sorted_donors[:20]]

# WebSocket listener
async def listen_websocket():
    global donation_totals
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                print("Connected to Pls Donate WebSocket!")
                while True:
                    raw = await ws.recv()
                    try:
                        event = json.loads(raw)
                        sender = event.get("sender")
                        amount = event.get("amount")
                        if sender and amount:
                            username = sender.get("username")
                            donation_totals[username] = donation_totals.get(username, 0) + amount
                            print(f"{username} donated {amount}. Total: {donation_totals[username]}")
                    except:
                        continue
        except Exception as e:
            print("WebSocket error, reconnecting in 3 seconds:", e)
            await asyncio.sleep(3)

# Run WebSocket listener in background thread
def start_ws_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_websocket())

threading.Thread(target=start_ws_loop, daemon=True).start()
