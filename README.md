## How to start
### Database and Redis
```bash
docker-compose up -d
```

### Backend
```bash
uv run run_server.py
```

### Frontend
```bash
npm run dev
```

### Delete volumes and restart
```bash
docker compose down -v
docker compose up -d --build
```

