# DeepChessIQ - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Node.js (v18+)
- SQL Server database running
- Backend environment configured

---

## 1️⃣ Backend Setup

```bash
cd backend
npm install
```

Create `.env` file in `backend/` directory:
```env
# Database
DB_SERVER=your-sql-server
DB_DATABASE=DeepChessIQ
DB_USER=your-username
DB_PASSWORD=your-password

# JWT
JWT_SECRET=your-secret-key-here

# SMTP (for emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
MAIL_FROM=noreply@deepchessiq.com

# Frontend URL (for CORS)
APP_PUBLIC_URL=http://localhost:5173

# Port
PORT=3000
```

Run database migrations:
```bash
# Execute the SQL files in order:
# 1. backend/src/db/migrations/001_invites_and_links.sql
# 2. backend/src/db/migrations/002_core_tables.sql
```

Start backend:
```bash
npm run dev
```

Backend will be running at: `http://localhost:3000`

---

## 2️⃣ Frontend Setup

```bash
cd chessiq-ui
npm install
```

Create `.env` file in `chessiq-ui/` directory:
```env
VITE_API_BASE_URL=http://localhost:3000
VITE_ENGINE_URL=http://20.55.88.222:8001/bestmove
VITE_ENGINE_TIMEOUT_MS=10000
```

Start frontend:
```bash
npm run dev
```

Frontend will be running at: `http://localhost:5173`

---

## 3️⃣ First Use

1. Open browser to `http://localhost:5173`
2. Click **"Register"**
3. Create a new account (choose "User" role)
4. You'll be automatically logged in
5. Go to **Dashboard** to see your stats
6. Click **"Play Now"** to start playing chess!

---

## 🎮 Features Available

### For All Users:
- ✅ Play chess against AI bot
- ✅ Games automatically saved
- ✅ View game history
- ✅ Track rating and statistics
- ✅ Customize game settings
- ✅ Edit profile
- ✅ Change password

### For Coaches:
- ✅ Access coach dashboard
- ✅ View students (static data currently)
- ✅ All user features

---

## 📚 API Endpoints

All backend APIs are documented in:
- `backend/API_DOCUMENTATION.md` - Complete API reference
- `backend/API_TEST_RESULTS.md` - Test results with examples

---

## 🐛 Troubleshooting

### Backend won't start
- Check SQL Server is running
- Verify database credentials in `.env`
- Ensure JWT_SECRET is set
- Check port 3000 is not in use

### Frontend can't connect to backend
- Verify backend is running at `http://localhost:3000`
- Check `VITE_API_BASE_URL` in frontend `.env`
- Check browser console for CORS errors
- Ensure `APP_PUBLIC_URL` in backend `.env` matches frontend URL

### Games not saving
- Check user is logged in
- Verify JWT token in localStorage
- Check browser console for errors
- Ensure `/api/games` endpoint is accessible

### No rating displayed
- Rating appears after playing at least one game
- Check `/api/statistics` endpoint is working
- Verify user has games in database

---

## 📖 Documentation

- `FRONTEND_BACKEND_INTEGRATION_COMPLETE.md` - Integration summary
- `INTEGRATION_CHECKLIST.md` - Detailed integration guide
- `backend/IMPLEMENTATION_SUMMARY.md` - Backend architecture
- `chessiq-ui/FRONTEND_IMPLEMENTATION_SUMMARY.md` - Frontend features

---

## 🆘 Need Help?

Check these files for detailed information:
1. Backend errors → `backend/IMPLEMENTATION_SUMMARY.md`
2. API usage → `backend/API_DOCUMENTATION.md`
3. Frontend features → `FRONTEND_BACKEND_INTEGRATION_COMPLETE.md`
4. Database setup → `backend/src/db/README.md`

---

## ✨ You're All Set!

Your DeepChessIQ application is now fully integrated and ready to use!

Enjoy playing chess! ♟️

