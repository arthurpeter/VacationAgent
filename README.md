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


## Deploy

### Create an environment variable with the encoded .env file
```bash
export ENCODED_ENV="hash"
```

### Run the deploy script
```bash
curl -sSL https://gist.githubusercontent.com/arthurpeter/42bd40166eca7e3594c2313d2fe95631/raw/8e94142b8e27076fc72c5f55e8d7b50815441703/deploy_turag.sh | bash
```
