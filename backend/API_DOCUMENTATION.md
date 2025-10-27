# DeepChessIQ Backend API Documentation

## Base URL
```
http://localhost:3000
```

## Authentication
Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Authentication Endpoints

### POST /auth/signup
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role_code": "user",
  "displayName": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role_code": "user",
    "display_name": "John Doe"
  }
}
```

### POST /auth/login
Log in an existing user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role_code": "user",
    "display_name": "John Doe"
  }
}
```

---

## Profile Endpoints

### GET /api/profile
Get current user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "John Doe",
  "role": "user",
  "bio": "Chess enthusiast",
  "avatarUrl": null,
  "country": "USA",
  "timezone": "America/New_York",
  "language": "en",
  "joinDate": "2025-01-15T10:30:00.000Z",
  "lastActive": "2025-10-27T14:20:00.000Z"
}
```

### PUT /api/profile
Update current user's profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "displayName": "Johnny Chess",
  "bio": "Passionate about chess",
  "country": "Canada",
  "timezone": "America/Toronto",
  "language": "en"
}
```

**Response:** `200 OK` (returns updated profile)

---

## Settings Endpoints

### GET /api/settings
Get user's settings.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "general": {
    "displayName": "John Doe",
    "email": "user@example.com",
    "language": "en",
    "timezone": "America/New_York"
  },
  "game": {
    "showLegalMoves": true,
    "highlightLastMove": true,
    "boardTheme": "classic",
    "pieceSet": "cburnett",
    "autoQueen": true,
    "soundEnabled": true
  }
}
```

### PUT /api/settings
Update user's settings.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "general": {
    "displayName": "New Name",
    "language": "es",
    "timezone": "Europe/Madrid"
  },
  "game": {
    "showLegalMoves": false,
    "highlightLastMove": true
  }
}
```

**Response:** `200 OK` (returns updated settings)

### POST /api/settings/change-password
Change user's password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "currentPassword": "oldpassword",
  "newPassword": "newpassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

---

## Statistics Endpoints

### GET /api/statistics
Get user's chess statistics.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "currentRating": 1520,
  "peakRating": 1620,
  "totalGamesPlayed": 127,
  "wins": 68,
  "losses": 45,
  "draws": 14,
  "winRatePercentage": 53.5,
  "currentStreak": {
    "type": "win",
    "count": 3
  },
  "averageGameDuration": "18 min",
  "gamesThisWeek": 12,
  "lastGameDate": "2025-10-27T14:00:00.000Z"
}
```

### GET /api/statistics/ratings/history
Get rating history for charts.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of records to return (default: 30)

**Response:** `200 OK`
```json
{
  "history": [
    {
      "rating": 1500,
      "ratingChange": 12,
      "date": "2025-10-20T10:00:00.000Z"
    },
    {
      "rating": 1512,
      "ratingChange": 8,
      "date": "2025-10-21T15:30:00.000Z"
    }
  ]
}
```

---

## Games Endpoints

### GET /api/games
Get user's game history.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `result` (optional): Filter by result ('win', 'loss', 'draw')
- `limit` (optional): Number of games to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "games": [
    {
      "id": "1",
      "date": "2025-10-27T14:00:00.000Z",
      "opponent": "ChessIQ Bot",
      "result": "win",
      "moves": 42,
      "opening": "Sicilian Defense",
      "timeControl": "10+0",
      "rating": 1520,
      "ratingChange": 12,
      "duration": "18 min"
    }
  ]
}
```

### GET /api/games/:id
Get specific game details including PGN.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "1",
  "date": "2025-10-27T14:00:00.000Z",
  "opponent": "ChessIQ Bot",
  "opponentType": "bot",
  "result": "win",
  "playerColor": "w",
  "moves": 42,
  "opening": "Sicilian Defense",
  "timeControl": "10+0",
  "rating": 1520,
  "ratingChange": 12,
  "pgn": "[Event \"ChessIQ Game\"]\n[White \"John Doe\"]\n...",
  "finalFen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "duration": "18 min"
}
```

### POST /api/games
Save a new game.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "result": "win",
  "userColor": "w",
  "totalMoves": 42,
  "openingName": "Sicilian Defense",
  "timeControl": "10+0",
  "ratingChange": 12,
  "pgn": "[Event \"ChessIQ Game\"]\n...",
  "finalFen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "durationSeconds": 1080,
  "opponentType": "bot",
  "opponentName": "ChessIQ Bot"
}
```

**Response:** `201 Created`
```json
{
  "message": "Game saved successfully",
  "gameId": "1",
  "newRating": 1532
}
```

### DELETE /api/games/:id
Delete a game.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "message": "Game deleted successfully"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid or missing authentication token"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "An internal server error occurred"
}
```

---

## Rate Limiting
Currently, no rate limiting is implemented. This should be added in production.

## CORS
The API accepts requests from:
- `http://localhost:5173` (Vite dev server)
- Additional origins can be configured via `APP_PUBLIC_URL` environment variable

---

## Database Schema

### Tables Created by Migration 002:
- `user_profiles` - Extended user information
- `chess_ratings` - Rating history tracking
- `games` - Game records
- `game_settings` - User preferences
- `user_statistics` - Computed statistics
- `invitations` - Coach invitation system
- `coach_students` - Coach-student relationships

---

## Testing the API

### Using curl:
```bash
# Register
curl -X POST http://localhost:3000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","displayName":"Test User"}'

# Login
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Get Profile (replace TOKEN)
curl -X GET http://localhost:3000/api/profile \
  -H "Authorization: Bearer TOKEN"
```

### Using Postman or Thunder Client:
1. Import the collection (create one from this documentation)
2. Set the `Authorization` header for protected routes
3. Test each endpoint

---

**Last Updated:** October 27, 2025

