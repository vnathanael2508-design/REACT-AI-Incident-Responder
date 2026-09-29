# RE:ACT — AI Incident Responder That Learns From Every Failure

RE:ACT is a Hindsight-powered incident investigation agent. Its core loop is **Recall → Decision → Outcome → Retain**.

## Run on Mac
```bash
cd REACT_Hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload
```
Open http://127.0.0.1:8000

## Hindsight
Set `HINDSIGHT_API_URL`, `HINDSIGHT_API_KEY`, and `HINDSIGHT_BANK_ID` in `.env`. Without credentials, the project runs transparently in Demo / Local Memory mode.

## Main features
Failure Fingerprint; Hindsight recall; failed-action memory; successful-fix memory; historical matching; memory-informed recommendations; learning-loop UI; demo dataset.

## Important
For final judging, configure Hindsight and demonstrate real memory recall/retention. The local fallback is for development and offline demonstration.
