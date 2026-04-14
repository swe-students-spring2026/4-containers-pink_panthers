![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
[![Web App CI](https://github.com/swe-students-spring2026/4-containers-pink_panthers/actions/workflows/web-ci.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-pink_panthers/actions/workflows/web-ci.yml)
[![ML Client CI](https://github.com/swe-students-spring2026/4-containers-pink_panthers/actions/workflows/ml-ci.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-pink_panthers/actions/workflows/ml-ci.yml)

# FitCheck 
Our web app helps users analyze if the outfit they are wearing has good color coordination. 
This way whether you are colorblind (or just have no sense of style) you can make sure your fit is great.

## Team Members:
- [Lily](https://github.com/lilylorand)
- [Sunil](https://github.com/SunilParab)
- [Calvin](https://github.com/CalvinPun)
- [Sean](https://github.com/seankimh)
- [Sara](https://github.com/SaraD-666)

## Setup and Configuration
### 1. Docker
Install and run [Docker](https://www.docker.com/get-started/) and create an account
### 2. Copy environment file
```bash
cp .env.example .env
cp web-app/.env.example web-app/.env
cp machine-learning-client/.env.example machine-learning-client/.env
```
### 3.Build and run containers
```bash
docker-compose up --build -d
```
### 4. Open web browser
Click [here](http://localhost:3000) 
Or open your browser and navigate to:
```text
http://localhost:3000
```
### 5.Stop containers when done
```bash
docker compose down
```

## Troubleshooting
- If containers fail to start, run:

```bash
docker compose down
docker compose up --build
```