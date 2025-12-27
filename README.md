# Bull vs Bear Royale - Python API

Python Flask backend API for Bull vs Bear Royale game, designed for Vercel deployment.

## Features

- RESTful API endpoints for game management
- Real-time game state updates via polling
- Player management (join, buy, sell, power-ups)
- Asset price simulation with market events
- Risk calculation and game results

## API Endpoints

### Health Check
- `GET /api/health` - Check API status

### Game Management
- `POST /api/game/join` - Join a game
  - Body: `{ "name": "PlayerName", "gameId": "optional" }`
  
- `GET /api/game/state?gameId=default` - Get current game state
  
- `POST /api/game/start` - Start the game
  - Body: `{ "gameId": "default" }`
  
- `POST /api/game/reset` - Reset the game
  - Body: `{ "gameId": "default" }`
  
- `GET /api/game/results?gameId=default` - Get game results

### Player Actions
- `POST /api/game/avatar` - Select avatar
  - Body: `{ "playerId": "...", "avatarId": "ANALYST", "gameId": "default" }`
  
- `POST /api/game/strategy` - Select strategy
  - Body: `{ "playerId": "...", "strategyId": "HIGH_ROLLER", "gameId": "default" }`
  
- `POST /api/game/buy` - Buy asset
  - Body: `{ "playerId": "...", "assetId": "AAPL", "amount": 1, "gameId": "default" }`
  
- `POST /api/game/sell` - Sell asset
  - Body: `{ "playerId": "...", "assetId": "AAPL", "amount": 1, "gameId": "default" }`
  
- `POST /api/game/powerup` - Use power-up
  - Body: `{ "playerId": "...", "powerUpId": "future-glimpse", "gameId": "default" }`

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python api/index.py
```

The API will be available at `http://localhost:5000`

## Vercel Deployment

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
cd python-api
vercel
```

3. For production:
```bash
vercel --prod
```

## Environment Variables

No environment variables required for basic functionality.

Optional:
- `GEMINI_API_KEY` - For AI-powered market events (not implemented in this version)

## Notes

- Game state is stored in memory (resets on deployment)
- For production, consider using Redis or a database
- Polling interval recommended: 1000ms (1 second)
- Maximum 50 price history points per asset
