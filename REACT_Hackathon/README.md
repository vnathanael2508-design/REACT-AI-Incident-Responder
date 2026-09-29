# RE:ACT — AI Incident Responder That Learns From Every Failure

RE:ACT is an AI-powered incident response system designed to help teams investigate technical incidents faster by learning from previous failures.

Instead of treating every incident as a new problem, RE:ACT uses **Hindsight memory** to remember previous incidents, successful fixes, failed approaches, and outcomes. This creates a continuous learning loop:

**Recall → Decision → Outcome → Retain**

---

## 🚀 Key Features

- 🔍 **AI-Powered Incident Investigation**
  - Analyze incidents based on severity and available information.

- 🧠 **Hindsight Memory**
  - Stores knowledge from previous incidents.
  - Recalls similar historical incidents and successful fixes.

- 🔗 **Incident Similarity & Recall**
  - Finds relevant past incidents based on current conditions.

- 💡 **Intelligent Recommendations**
  - Suggests possible fixes using previous successful resolutions.

- 📊 **Incident Analysis**
  - Displays incident severity, historical matches, and recommendations.

- 🔄 **Continuous Learning**
  - Records the outcome of every investigation so future recommendations can improve.

---

## 🧠 How Hindsight Is Used

Hindsight acts as the **memory layer** of RE:ACT.

When a new incident occurs, RE:ACT:

1. **Recalls** similar incidents from memory.
2. **Analyzes** what actions were previously taken.
3. **Recommends** an appropriate response.
4. **Records the outcome** after the incident is resolved.
5. **Retains the experience** for future incidents.

This allows the system to learn from both successful and unsuccessful troubleshooting experiences.

---

## 🔄 RE:ACT Learning Loop

```text
New Incident
     ↓
   Recall
     ↓
Similar Past Incidents
     ↓
   Decision
     ↓
Recommended Action
     ↓
   Outcome
     ↓
Was the incident resolved?
     ↓
   Retain
     ↓
Memory Updated
🏗️ Project Structure
REACT_Hackathon/
│
├── data/
│   └── Incident and memory data
│
├── docs/
│   └── Project documentation
│
├── static/
│   └── Frontend/static assets
│
├── app.py
│   └── Main application
│
├── requirements.txt
│   └── Python dependencies
│
├── .env.example
│   └── Environment variable template
│
├── .gitignore
│   └── Git ignored files
│
└── README.md
    └── Project documentation
⚙️ Technologies Used
Python
FastAPI
Hindsight Memory
HTML
CSS
JavaScript
REST APIs
AI-powered incident analysis
🖥️ Running the Project Locally
1. Clone the repository
git clone https://github.com/vnathanael2508-design/REACT-AI-Incident-Responder.git
cd REACT-AI-Incident-Responder
2. Create a virtual environment
python3 -m venv venv
3. Activate the environment

macOS / Linux:

source venv/bin/activate

Windows:

venv\Scripts\activate
4. Install dependencies
pip install -r requirements.txt
5. Configure environment variables

Create a .env file using .env.example as a reference.

Add the required API keys and configuration values.

6. Start the application
uvicorn app:app --reload
7. Open the application

Visit:

http://127.0.0.1:8000
🎯 Example Use Case
Incident
SEV-1: Production API is returning 500 errors.

RE:ACT searches its memory for similar incidents.

It may find:

Previous Incident:
API failures caused by database connection exhaustion.

Successful Fix:
Restart connection pool and increase connection limit.

RE:ACT uses this historical experience to provide a recommendation for the current investigation.

After the incident is resolved, the result is stored back into memory.

🌟 Why RE:ACT?

Traditional incident response often depends on engineers remembering what happened previously.

RE:ACT turns those experiences into reusable organizational memory.

Every incident becomes an opportunity to learn.

Recall what happened.
Decide what to do.
Observe the outcome.
Retain the learning.

🔐 Security
Sensitive credentials should be stored in environment variables.
.env files should never be committed to GitHub.
API keys and secrets must not be hard-coded in source code.
📌 Project

RE:ACT — AI Incident Responder That Learns From Every Failure

Built for a hackathon using Hindsight memory to create a continuously learning incident-response workflow.

👨‍💻 Repository

GitHub:
https://github.com/vnathanael2508-design/REACT-AI-Incident-Responder
