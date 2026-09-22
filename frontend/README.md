# Frontend — Movie Recommendation System UI

Interactive React + Vite interface with modern UI for discovering, filtering, and receiving hybrid movie recommendations.

---

## 📁 Directory Structure

```
frontend/
├── public/              # Static assets (favicons, SVGs)
├── src/
│   ├── components/      # UI components (MovieCard, SearchBar, Sliders, RecModal)
│   ├── services/
│   │   └── api.js       # Central API client communicating with backend /api endpoints
│   ├── App.jsx          # Main application dashboard
│   ├── index.css        # Styling and design system
│   └── main.jsx         # React DOM entrypoint
├── .env.example         # Template for environment configuration
├── Dockerfile           # Frontend Nginx containerization
├── package.json         # Scripts and dependencies
├── vite.config.js       # Vite bundler & backend proxy configuration
└── README.md
```

---

## 🚀 Quickstart (Standalone)

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

The frontend will run at `http://localhost:5173`.

---

## 🔗 Linking with Backend

Communication between the frontend and backend is handled seamlessly across all environments:

1. **Local Development (Default - Proxy Mode)**:
   - In `vite.config.js`, Vite proxies all requests starting with `/api` to `http://127.0.0.1:8000`.
   - You can just run `npm run dev` and all requests to `/api/*` automatically hit the local FastAPI backend.

2. **Connecting to a Remote or Custom Backend**:
   - Create a `frontend/.env` file:
     ```env
     VITE_API_BASE_URL=https://your-custom-backend-url.com
     ```
   - In `src/services/api.js`, `API_BASE_URL` will prefix all endpoint requests with this URL.

3. **Production / Vercel**:
   - `vercel.json` rewrites `/api/*` requests to the Python serverless backend and routes all other paths to the built React static files.
