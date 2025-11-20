# Frontend-Backend Integration Checklist

## ✅ Backend Setup Complete
- [x] Database migration executed (002_core_tables.sql)
- [x] All API routes implemented and tested
- [x] Authentication middleware working
- [x] CORS configured for frontend (localhost:5173)
- [x] Backend server running on port 3000

---

## 📋 Frontend Integration Tasks

### 1. Environment Variables Setup
**File:** `chessiq-ui/.env`

```env
VITE_API_BASE_URL=http://localhost:3000
VITE_ENGINE_URL=http://20.55.88.222:8001/bestmove
VITE_ENGINE_TIMEOUT_MS=10000
```

**Status:** ⏳ Pending

---

### 2. Authentication (Already Integrated) ✅
**Files:** 
- `AuthContext.tsx` - Already using backend APIs
- `SignIn.tsx` - Already connected
- `Register.tsx` - Already connected

**Endpoints Used:**
- ✅ `POST /auth/signup`
- ✅ `POST /auth/login`

---

### 3. Profile Page Integration
**File:** `chessiq-ui/src/pages/Profile.tsx`

**Endpoints to Integrate:**
- `GET /api/profile` - Fetch user profile
- `PUT /api/profile` - Update profile info

**Current Status:** ⏳ Not yet created
**Priority:** High

**Implementation Steps:**
1. Create Profile.tsx page
2. Fetch profile data on mount
3. Display editable form fields:
   - Display Name
   - Bio
   - Country
   - Timezone
   - Language
4. Implement save functionality
5. Show success/error messages

---

### 4. Settings Page Integration
**File:** `chessiq-ui/src/pages/Settings.tsx`

**Endpoints to Integrate:**
- `GET /api/settings` - Fetch settings
- `PUT /api/settings` - Update settings
- `POST /api/settings/change-password` - Change password

**Current Status:** ⏳ Not yet created
**Priority:** High

**Implementation Steps:**
1. Create Settings.tsx page
2. Fetch settings on mount
3. Create tabs for:
   - Game Settings (show legal moves, highlight last move)
   - Account Settings (display name, email, language)
   - Security (change password)
4. Implement save functionality for each section
5. Show confirmation messages

---

### 5. Game Library Integration
**File:** `chessiq-ui/src/pages/GameLibrary.tsx`

**Endpoints to Integrate:**
- `GET /api/games` - Fetch game history
- `GET /api/games/:id` - Get specific game details
- `DELETE /api/games/:id` - Delete game (optional)

**Current Status:** ✅ Page exists but uses mock data
**Priority:** High

**Implementation Steps:**
1. Replace mock data with API call
2. Implement pagination (limit/offset)
3. Add filter by result (win/loss/draw)
4. Implement game detail modal with PGN viewer
5. Add delete game functionality

---

### 6. Dashboard Statistics Integration
**File:** `chessiq-ui/src/components/dashboard/Dashboard.tsx`

**Endpoints to Integrate:**
- `GET /api/statistics` - Fetch user statistics

**Current Status:** ⏳ Using static/mock data
**Priority:** Medium

**Implementation Steps:**
1. Fetch statistics on mount
2. Display real data:
   - Current Rating
   - Total Games
   - Win/Loss/Draw counts
   - Win Rate
   - Current Streak
   - Games This Week
3. Add loading states
4. Handle errors gracefully

---

### 7. Save Game After Match
**File:** `chessiq-ui/src/pages/Home.tsx` or `chessiq-ui/src/hooks/useChessGame.ts`

**Endpoint to Integrate:**
- `POST /api/games` - Save completed game

**Current Status:** ⏳ Games not being saved
**Priority:** High

**Implementation Steps:**
1. Detect game over state
2. Calculate game stats:
   - Total moves
   - Duration in seconds
   - Result (win/loss/draw)
   - User color
   - Opening name (if available)
3. Extract PGN from chess.js
4. Send POST request to save game
5. Show confirmation message
6. Update local statistics

---

### 8. Rating Display Integration
**File:** Multiple locations

**Endpoints to Integrate:**
- `GET /api/statistics` - Get current rating
- `GET /api/statistics/ratings/history` - Get rating chart data

**Locations to Update:**
1. Navbar - Show current rating badge
2. Profile page - Show rating history chart
3. Dashboard - Show rating progress

**Current Status:** ⏳ Not implemented
**Priority:** Medium

---

## 🔧 Technical Implementation Notes

### API Helper Function (Already Exists in AuthContext)
```typescript
async function postJSON<T = any>(url: string, body: any): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}
```

### Authenticated API Calls
For protected endpoints, include the JWT token:

```typescript
const token = user?.token // from AuthContext

const response = await fetch(`${API_BASE}/api/profile`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

### Create a Shared API Service (Recommended)
**File:** `chessiq-ui/src/services/api.ts`

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('chess-session')
  const user = token ? JSON.parse(token) : null
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(user?.token && { 'Authorization': `Bearer ${user.token}` }),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

// Profile API
export const profileApi = {
  get: () => apiRequest('/api/profile'),
  update: (data: any) => apiRequest('/api/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
}

// Settings API
export const settingsApi = {
  get: () => apiRequest('/api/settings'),
  update: (data: any) => apiRequest('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  changePassword: (data: any) => apiRequest('/api/settings/change-password', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
}

// Games API
export const gamesApi = {
  list: (params?: { result?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams(params as any).toString()
    return apiRequest(`/api/games${query ? `?${query}` : ''}`)
  },
  get: (id: string) => apiRequest(`/api/games/${id}`),
  save: (data: any) => apiRequest('/api/games', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  delete: (id: string) => apiRequest(`/api/games/${id}`, {
    method: 'DELETE',
  }),
}

// Statistics API
export const statisticsApi = {
  get: () => apiRequest('/api/statistics'),
  ratingHistory: (limit = 30) => 
    apiRequest(`/api/statistics/ratings/history?limit=${limit}`),
}
```

---

## 🧪 Testing Checklist

### Manual Testing Steps:
1. [ ] Start backend server: `cd backend && npm run dev`
2. [ ] Start frontend: `cd chessiq-ui && npm run dev`
3. [ ] Register new user
4. [ ] Login with user credentials
5. [ ] View profile page
6. [ ] Update profile information
7. [ ] Change game settings
8. [ ] Play a game to completion
9. [ ] Verify game saved in Game Library
10. [ ] Check statistics updated on Dashboard
11. [ ] View rating history chart
12. [ ] Test PGN export/import
13. [ ] Logout and login again
14. [ ] Verify data persists

---

## 🚀 Deployment Checklist

### Backend:
- [ ] Update environment variables for production
- [ ] Configure production database connection
- [ ] Set secure JWT_SECRET
- [ ] Configure SMTP for production emails
- [ ] Set APP_PUBLIC_URL to production frontend URL
- [ ] Enable HTTPS

### Frontend:
- [ ] Update VITE_API_BASE_URL to production backend
- [ ] Build production bundle: `npm run build`
- [ ] Test production build locally
- [ ] Deploy to hosting service
- [ ] Verify all API calls work in production

---

## 📝 Implementation Priority

### Phase 1 (High Priority):
1. Create shared API service (`api.ts`)
2. Integrate Save Game functionality
3. Update Dashboard with real statistics
4. Connect Game Library to backend

### Phase 2 (Medium Priority):
1. Create Profile page
2. Create Settings page
3. Add rating history charts
4. Display rating in navbar

### Phase 3 (Nice to Have):
1. Game replay functionality
2. Advanced filtering in Game Library
3. Export statistics as CSV
4. Share game links

---

## 🐛 Common Issues & Solutions

### CORS Errors:
- Ensure backend CORS is configured for `http://localhost:5173`
- Check `src/index.js` for CORS middleware

### Authentication Errors:
- Verify JWT token is stored in localStorage
- Check token expiration (12 hours default)
- Ensure Authorization header format: `Bearer <token>`

### 404 Errors:
- Verify API_BASE_URL is set correctly
- Check backend server is running
- Confirm route paths match API documentation

### Database Errors:
- Run migration script if tables don't exist
- Check SQL Server connection in `.env`
- Verify foreign key constraints (UNIQUEIDENTIFIER)

---

## 📚 Additional Resources

- **API Documentation:** `backend/API_DOCUMENTATION.md`
- **Test Results:** `backend/API_TEST_RESULTS.md`
- **Backend Implementation:** `backend/IMPLEMENTATION_SUMMARY.md`
- **Frontend Features:** `chessiq-ui/FRONTEND_IMPLEMENTATION_SUMMARY.md`

