# Banking app


## Install

Requires Docker and Compose. Will use ´./data´ folder to persist data (database and ML models).

Start the app:

```bash
docker compose pull
docker compose up -d 
```

# Devlopment env

A working dev environment can be started with helper scripts:

```
./scripts/dev-launch-env.sh
```

And can be stopped with:

```
# also deletes dev data
./scripts/dev-stop-env.sh
```

# Security disclaimer
This app stores sensitive banking transactions history information that you upload. Please only deploy this application if you know what you are doing.
