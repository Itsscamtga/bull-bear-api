from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional
import threading

app = Flask(__name__)
CORS(app)

# Global game state storage (in production, use Redis or database)
game_states: Dict[str, dict] = {}
game_locks: Dict[str, threading.Lock] = {}

# Constants
GAME_ROUNDS = 5
ROUND_DURATION_MS = 35000
STARTING_CASH = 10000
TOTAL_FRAMES = 35

# Initial Assets Data
INITIAL_ASSETS = [
    {
        "id": "AAPL",
        "name": "Apple Inc.",
        "type": "STOCK",
        "baseVolatility": 0.8,
        "trendBias": "UP",
        "currentPrice": 150.0,
        "history": [150.0]
    },
    {
        "id": "BTC",
        "name": "Bitcoin",
        "type": "CRYPTO",
        "baseVolatility": 2.5,
        "trendBias": "SIDEWAYS",
        "currentPrice": 45000.0,
        "history": [45000.0]
    },
    {
        "id": "GOVT",
        "name": "Government Bonds",
        "type": "BOND",
        "baseVolatility": 0.3,
        "trendBias": "SIDEWAYS",
        "currentPrice": 100.0,
        "history": [100.0]
    },
    {
        "id": "SPY",
        "name": "S&P 500 ETF",
        "type": "ETF",
        "baseVolatility": 0.6,
        "trendBias": "UP",
        "currentPrice": 400.0,
        "history": [400.0]
    }
]

AVATARS = [
    {
        "id": "ANALYST",
        "name": "The Analyst",
        "description": "Data-driven decision maker",
        "effectDescription": "Better risk assessment"
    },
    {
        "id": "DEGEN",
        "name": "The Degen",
        "description": "High risk, high reward",
        "effectDescription": "Bonus on volatile assets"
    },
    {
        "id": "STRATEGIST",
        "name": "The Strategist",
        "description": "Long-term planner",
        "effectDescription": "Reduced fees"
    },
    {
        "id": "MEME_LORD",
        "name": "The Meme Lord",
        "description": "Rides the hype",
        "effectDescription": "Sentiment bonus"
    }
]

STRATEGIES = [
    {
        "id": "HIGH_ROLLER",
        "name": "High Roller",
        "bonusDescription": "+15% on wins",
        "tooltip": "High risk, high reward"
    },
    {
        "id": "SAFETY_FIRST",
        "name": "Safety First",
        "bonusDescription": "-10% risk score",
        "tooltip": "Conservative approach"
    },
    {
        "id": "DIVERSIFIER",
        "name": "Diversifier",
        "bonusDescription": "+5% if 4+ assets",
        "tooltip": "Spread your bets"
    },
    {
        "id": "SWING_TRADER",
        "name": "Swing Trader",
        "bonusDescription": "Quick profit bonus",
        "tooltip": "Buy low, sell high"
    }
]

SCENARIOS = [
    {
        "id": "BULL_RUN",
        "title": "Bull Market Rally",
        "description": "Markets are soaring!",
        "effectDescription": "Increased volatility"
    },
    {
        "id": "BEAR_CRASH",
        "title": "Bear Market Crash",
        "description": "Markets are plummeting!",
        "effectDescription": "High risk environment"
    },
    {
        "id": "SIDEWAYS",
        "title": "Sideways Market",
        "description": "Markets are stable",
        "effectDescription": "Low volatility"
    }
]


def create_new_game(game_id: str = "default") -> dict:
    """Create a new game state"""
    return {
        "id": game_id,
        "players": [],
        "assets": json.loads(json.dumps(INITIAL_ASSETS)),
        "currentRound": 0,
        "maxRounds": GAME_ROUNDS,
        "activeEvent": None,
        "phase": "PRE_MATCH",
        "subPhase": "INTRO",
        "timeRemaining": 0,
        "activeAssetType": "ALL",
        "activeScenario": None,
        "fearZoneActive": False,
        "sentiment": {
            "STOCK": 0,
            "CRYPTO": 0,
            "BOND": 0,
            "ETF": 0
        },
        "roundStartTime": None,
        "lastUpdate": time.time()
    }


def get_game_state(game_id: str = "default") -> dict:
    """Get or create game state"""
    if game_id not in game_states:
        game_states[game_id] = create_new_game(game_id)
        game_locks[game_id] = threading.Lock()
    return game_states[game_id]


def create_player(player_id: str, name: str) -> dict:
    """Create a new player"""
    return {
        "id": player_id,
        "name": name,
        "cash": STARTING_CASH,
        "holdings": [],
        "riskScore": 0,
        "powerUps": [
            {"id": "future-glimpse", "name": "Risk Shield", "description": "-20 Risk Score", "usesLeft": 1},
            {"id": "market-freeze", "name": "Bailout", "description": "+$1000 Cash", "usesLeft": 1}
        ],
        "totalValue": STARTING_CASH,
        "ready": False,
        "transactionLog": [],
        "avatarId": None,
        "strategyId": None
    }


def calculate_risk(player: dict, assets: List[dict]) -> int:
    """Calculate player risk score"""
    total_risk = 0
    total_portfolio_value = 0
    
    for holding in player["holdings"]:
        asset = next((a for a in assets if a["id"] == holding["assetId"]), None)
        if asset:
            value = holding["quantity"] * asset["currentPrice"]
            total_portfolio_value += value
            total_risk += value * asset["baseVolatility"] * 500
    
    if total_portfolio_value > 0:
        risk_score = min(100, round(total_risk / total_portfolio_value * 100))
        if player.get("strategyId") == "SAFETY_FIRST":
            risk_score = max(0, risk_score - 10)
        return risk_score
    return 0


def update_prices(game_state: dict):
    """Update asset prices based on market conditions"""
    for asset in game_state["assets"]:
        change = 0
        
        # News impact
        if game_state["activeEvent"] and game_state["activeEvent"].get("impact"):
            impact = game_state["activeEvent"]["impact"].get(asset["type"], 0)
            if impact != 0:
                change += impact / TOTAL_FRAMES
        
        # Volatility
        vol_multiplier = 1.0
        if game_state["activeEvent"] and game_state["activeEvent"].get("volatility_multiplier"):
            vol_multiplier = game_state["activeEvent"]["volatility_multiplier"]
        
        random_movement = (random.random() - 0.5) * 0.015 * asset["baseVolatility"] * vol_multiplier
        change += random_movement
        
        # Sentiment drift
        sentiment = game_state["sentiment"][asset["type"]]
        sentiment_drift = (sentiment / 100) * (0.05 / TOTAL_FRAMES)
        change += sentiment_drift
        
        # Apply update
        asset["currentPrice"] = asset["currentPrice"] * (1 + change)
        asset["history"].append(asset["currentPrice"])
        if len(asset["history"]) > 50:
            asset["history"].pop(0)
    
    # Update player total values
    for player in game_state["players"]:
        holdings_value = 0
        for holding in player["holdings"]:
            asset = next((a for a in game_state["assets"] if a["id"] == holding["assetId"]), None)
            if asset:
                holdings_value += holding["quantity"] * asset["currentPrice"]
        player["totalValue"] = player["cash"] + holdings_value
        player["riskScore"] = calculate_risk(player, game_state["assets"])


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": time.time()})


@app.route('/api/game/join', methods=['POST'])
def join_game():
    """Join a game"""
    data = request.json
    name = data.get('name')
    game_id = data.get('gameId', 'default')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        # Check if player already exists
        existing_player = next((p for p in game_state["players"] if p["name"] == name), None)
        
        if existing_player:
            player_id = existing_player["id"]
        else:
            player_id = f"player-{len(game_state['players'])}-{int(time.time())}"
            new_player = create_player(player_id, name)
            game_state["players"].append(new_player)
        
        game_state["lastUpdate"] = time.time()
    
    return jsonify({
        "playerId": player_id,
        "gameId": game_id,
        "gameState": game_state
    })


@app.route('/api/game/state', methods=['GET'])
def get_state():
    """Get current game state"""
    game_id = request.args.get('gameId', 'default')
    game_state = get_game_state(game_id)
    
    # Auto-update if in PLAYING phase
    if game_state["phase"] == "PLAYING" and game_state["roundStartTime"]:
        elapsed = time.time() - game_state["roundStartTime"]
        time_remaining = max(0, TOTAL_FRAMES - int(elapsed))
        game_state["timeRemaining"] = time_remaining
        
        # Update prices if market is active (after news phase)
        if time_remaining < 30:
            update_prices(game_state)
        
        # Check if round ended
        if time_remaining <= 0:
            with game_locks[game_id]:
                if game_state["currentRound"] < game_state["maxRounds"]:
                    game_state["currentRound"] += 1
                    game_state["roundStartTime"] = time.time()
                    game_state["timeRemaining"] = TOTAL_FRAMES
                else:
                    game_state["phase"] = "FINISHED"
                    game_state["roundStartTime"] = None
    
    return jsonify(game_state)


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Start the game"""
    data = request.json
    game_id = data.get('gameId', 'default')
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        if game_state["phase"] == "PRE_MATCH":
            # Skip pre-match for simplicity, go straight to playing
            game_state["phase"] = "PLAYING"
            game_state["currentRound"] = 1
            game_state["roundStartTime"] = time.time()
            game_state["timeRemaining"] = TOTAL_FRAMES
            
            # Pick random scenario
            game_state["activeScenario"] = random.choice(SCENARIOS)
            
            game_state["lastUpdate"] = time.time()
    
    return jsonify(game_state)


@app.route('/api/game/avatar', methods=['POST'])
def select_avatar():
    """Select avatar"""
    data = request.json
    player_id = data.get('playerId')
    avatar_id = data.get('avatarId')
    game_id = data.get('gameId', 'default')
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        player = next((p for p in game_state["players"] if p["id"] == player_id), None)
        if player:
            player["avatarId"] = avatar_id
            game_state["lastUpdate"] = time.time()
    
    return jsonify(game_state)


@app.route('/api/game/strategy', methods=['POST'])
def select_strategy():
    """Select strategy"""
    data = request.json
    player_id = data.get('playerId')
    strategy_id = data.get('strategyId')
    game_id = data.get('gameId', 'default')
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        player = next((p for p in game_state["players"] if p["id"] == player_id), None)
        if player:
            player["strategyId"] = strategy_id
            game_state["lastUpdate"] = time.time()
    
    return jsonify(game_state)


@app.route('/api/game/buy', methods=['POST'])
def buy_asset():
    """Buy an asset"""
    data = request.json
    player_id = data.get('playerId')
    asset_id = data.get('assetId')
    amount = data.get('amount', 1)
    game_id = data.get('gameId', 'default')
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        player = next((p for p in game_state["players"] if p["id"] == player_id), None)
        asset = next((a for a in game_state["assets"] if a["id"] == asset_id), None)
        
        if not player or not asset or game_state["phase"] != "PLAYING":
            return jsonify({"error": "Invalid request"}), 400
        
        cost = amount * asset["currentPrice"]
        if player["cash"] >= cost:
            player["cash"] -= cost
            
            holding = next((h for h in player["holdings"] if h["assetId"] == asset_id), None)
            if holding:
                total_cost = (holding["quantity"] * holding["avgBuyPrice"]) + cost
                holding["quantity"] += amount
                holding["avgBuyPrice"] = total_cost / holding["quantity"]
            else:
                player["holdings"].append({
                    "assetId": asset_id,
                    "quantity": amount,
                    "avgBuyPrice": asset["currentPrice"]
                })
            
            player["transactionLog"].append({
                "round": game_state["currentRound"],
                "type": "BUY",
                "assetId": asset_id,
                "assetType": asset["type"],
                "amount": amount,
                "price": asset["currentPrice"],
                "totalValue": cost,
                "eventActive": game_state["activeEvent"]["id"] if game_state["activeEvent"] else None,
                "sentimentAtTime": game_state["sentiment"][asset["type"]]
            })
            
            game_state["lastUpdate"] = time.time()
            return jsonify({"success": True, "gameState": game_state})
        else:
            return jsonify({"error": "Insufficient funds"}), 400


@app.route('/api/game/sell', methods=['POST'])
def sell_asset():
    """Sell an asset"""
    data = request.json
    player_id = data.get('playerId')
    asset_id = data.get('assetId')
    amount = data.get('amount', 1)
    game_id = data.get('gameId', 'default')
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        player = next((p for p in game_state["players"] if p["id"] == player_id), None)
        asset = next((a for a in game_state["assets"] if a["id"] == asset_id), None)
        
        if not player or not asset or game_state["phase"] != "PLAYING":
            return jsonify({"error": "Invalid request"}), 400
        
        holding = next((h for h in player["holdings"] if h["assetId"] == asset_id), None)
        if holding and holding["quantity"] >= amount:
            revenue = amount * asset["currentPrice"]
            player["cash"] += revenue
            holding["quantity"] -= amount
            
            if holding["quantity"] <= 0:
                player["holdings"] = [h for h in player["holdings"] if h["assetId"] != asset_id]
            
            player["transactionLog"].append({
                "round": game_state["currentRound"],
                "type": "SELL",
                "assetId": asset_id,
                "assetType": asset["type"],
                "amount": amount,
                "price": asset["currentPrice"],
                "totalValue": revenue,
                "eventActive": game_state["activeEvent"]["id"] if game_state["activeEvent"] else None,
                "sentimentAtTime": game_state["sentiment"][asset["type"]]
            })
            
            game_state["lastUpdate"] = time.time()
            return jsonify({"success": True, "gameState": game_state})
        else:
            return jsonify({"error": "Insufficient holdings"}), 400


@app.route('/api/game/powerup', methods=['POST'])
def use_powerup():
    """Use a power-up"""
    data = request.json
    player_id = data.get('playerId')
    powerup_id = data.get('powerUpId')
    game_id = data.get('gameId', 'default')
    
    game_state = get_game_state(game_id)
    
    with game_locks[game_id]:
        player = next((p for p in game_state["players"] if p["id"] == player_id), None)
        
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        powerup = next((p for p in player["powerUps"] if p["id"] == powerup_id), None)
        if not powerup or powerup["usesLeft"] <= 0:
            return jsonify({"error": "Power-up not available"}), 400
        
        powerup["usesLeft"] -= 1
        
        if powerup_id == "future-glimpse":
            player["riskScore"] = max(0, player["riskScore"] - 20)
        elif powerup_id == "market-freeze":
            player["cash"] += 1000
        
        game_state["lastUpdate"] = time.time()
    
    return jsonify({"success": True, "gameState": game_state})


@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Reset/restart the game"""
    data = request.json
    game_id = data.get('gameId', 'default')
    
    with game_locks.get(game_id, threading.Lock()):
        game_states[game_id] = create_new_game(game_id)
    
    return jsonify(game_states[game_id])


@app.route('/api/game/results', methods=['GET'])
def get_results():
    """Get game results"""
    game_id = request.args.get('gameId', 'default')
    game_state = get_game_state(game_id)
    
    if game_state["phase"] != "FINISHED":
        return jsonify({"error": "Game not finished"}), 400
    
    results = []
    for player in game_state["players"]:
        initial_value = STARTING_CASH
        final_value = player["totalValue"]
        
        # Strategy bonus
        if player.get("strategyId") == "DIVERSIFIER":
            unique_assets = len(set(h["assetId"] for h in player["holdings"]))
            if unique_assets >= 4:
                final_value += final_value * 0.05
        
        roi = ((final_value - initial_value) / initial_value) * 100
        risk_adjusted_score = roi - (player["riskScore"] * 0.5)
        
        results.append({
            "playerId": player["id"],
            "playerName": player["name"],
            "finalValue": final_value,
            "riskScore": player["riskScore"],
            "roi": roi,
            "riskAdjustedScore": risk_adjusted_score,
            "rank": 0,
            "insights": ["Great job!", "Keep learning!"],
            "playerSummary": {
                "whatYouDidWell": ["You participated actively"],
                "mistakesAndOpportunities": ["Consider diversifying more"],
                "improvementSuggestions": ["Try different strategies"]
            },
            "learningCards": []
        })
    
    # Sort by risk-adjusted score
    results.sort(key=lambda x: x["riskAdjustedScore"], reverse=True)
    for i, result in enumerate(results):
        result["rank"] = i + 1
    
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
