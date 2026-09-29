import os
import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ============================================================
# OPTIONAL DOTENV
# ============================================================

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================
# HINDSIGHT
# ============================================================

try:
    from hindsight_client import Hindsight
    HINDSIGHT_AVAILABLE = True
except ImportError:
    Hindsight = None
    HINDSIGHT_AVAILABLE = False


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "incidents.json"

STATIC_DIR = BASE_DIR / "static"

DATA_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="RE:ACT",
    description="AI Incident Response with Hindsight Memory",
    version="2.0.0"
)


# ============================================================
# HINDSIGHT CONFIGURATION
# ============================================================

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    os.getenv(
        "HINDSIGHT_API_URL",
        "http://localhost:8888"
    )
)

HINDSIGHT_API_KEY = os.getenv(
    "HINDSIGHT_API_KEY",
    ""
)

HINDSIGHT_BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID",
    "react-incident-memory"
)


# ============================================================
# GLOBAL HINDSIGHT CLIENT
# ============================================================

hindsight_client = None

hindsight_connected = False


# ============================================================
# MEMORY STATE
# ============================================================

memory_state = {
    "initialized": False,
    "hindsight_connected": False,
    "last_updated": None
}


# ============================================================
# INCIDENT MODEL
# ============================================================

class Incident(BaseModel):

    service: str

    title: str

    severity: str

    symptoms: str

    logs: str = ""

    root_cause: str = ""

    attempted_actions: str = ""

    failed_actions: str = ""

    successful_fix: str = ""

    resolution_minutes: int = 0

    recent_change: str = ""


# ============================================================
# DEMO INCIDENTS
# ============================================================

DEMO_INCIDENTS = [

    {
        "service": "Payments API",

        "title": "Payment API database connection timeout",

        "severity": "SEV-1",

        "symptoms": (
            "Payment requests are failing with 500 errors. "
            "Database connection timeout. "
            "Connection pool exhausted."
        ),

        "logs": (
            "ERROR PaymentService: database connection timeout\n"
            "ERROR ConnectionPool: unable to acquire connection\n"
            "HTTP 500 POST /api/payment\n"
            "Connection pool exhausted"
        ),

        "root_cause": (
            "Database connection pool was exhausted."
        ),

        "attempted_actions": (
            "Restarted the Payments API."
        ),

        "failed_actions": (
            "Repeated application restarts did not resolve "
            "the database connection issue."
        ),

        "successful_fix": (
            "Increased the database connection pool and "
            "restarted the affected service."
        ),

        "resolution_minutes": 18,

        "recent_change": (
            "Database connection pool configuration was "
            "changed during the latest deployment."
        )
    },

    {
        "service": "Railway Booking API",

        "title": "Passengers charged but tickets not generated",

        "severity": "SEV-1",

        "symptoms": (
            "Passengers are successfully charged, but ticket "
            "confirmations are delayed or missing. "
            "Some users receive duplicate payment notifications."
        ),

        "logs": (
            "ERROR BookingService: ticket generation timeout\n"
            "ERROR PaymentService: payment completed successfully\n"
            "WARN BookingQueue: message processing delayed\n"
            "ERROR BookingService: booking confirmation not received\n"
            "WARN QueueConsumer: retry limit reached"
        ),

        "root_cause": (
            "Booking messages were stuck between the payment "
            "service and booking queue."
        ),

        "attempted_actions": (
            "Restarted the Booking API."
        ),

        "failed_actions": (
            "Restarting the Booking API did not resolve the issue."
        ),

        "successful_fix": (
            "Reprocessed the booking queue and corrected "
            "the payment gateway configuration."
        ),

        "resolution_minutes": 24,

        "recent_change": (
            "New payment gateway integration was deployed."
        )
    },

    {
        "service": "Authentication Service",

        "title": "Users unable to login after deployment",

        "severity": "SEV-2",

        "symptoms": (
            "Users are unable to login. Authentication requests "
            "return 401 errors. Token validation is failing."
        ),

        "logs": (
            "ERROR AuthService: invalid token signature\n"
            "ERROR JWT: signature verification failed\n"
            "HTTP 401 POST /api/login\n"
            "WARN Authentication middleware rejected request"
        ),

        "root_cause": (
            "Authentication signing configuration became "
            "inconsistent after deployment."
        ),

        "attempted_actions": (
            "Restarted the authentication service."
        ),

        "failed_actions": (
            "Restarting the authentication service did not "
            "resolve the invalid token signature errors."
        ),

        "successful_fix": (
            "Rolled back the authentication deployment and "
            "regenerated the signing configuration."
        ),

        "resolution_minutes": 15,

        "recent_change": (
            "A new authentication service version was deployed."
        )
    },

    {
        "service": "Redis Cache Service",

        "title": "Redis cache timeout causing slow API responses",

        "severity": "SEV-2",

        "symptoms": (
            "API requests are taking longer than normal. "
            "Redis requests are timing out and cache hit rate dropped."
        ),

        "logs": (
            "ERROR RedisClient: connection timeout\n"
            "WARN CacheService: Redis unavailable\n"
            "WARN API latency exceeded threshold\n"
            "ERROR RedisPool: unable to acquire connection"
        ),

        "root_cause": (
            "Redis connection pool reached its configured limit."
        ),

        "attempted_actions": (
            "Restarted the API service."
        ),

        "failed_actions": (
            "Restarting the API did not resolve the Redis timeout."
        ),

        "successful_fix": (
            "Increased the Redis connection pool limit and "
            "restarted the affected workers."
        ),

        "resolution_minutes": 21,

        "recent_change": (
            "Traffic increased significantly after the latest release."
        )
    }
]


# ============================================================
# LOCAL STORAGE
# ============================================================

def load_local_incidents() -> List[dict]:

    if not DATA_FILE.exists():

        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):

            return data

        return []

    except Exception:

        return []


def save_local_incidents(
    incidents: List[dict]
):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            incidents,
            file,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

STOP_WORDS = {
    "the",
    "and",
    "or",
    "a",
    "an",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "was",
    "are",
    "were",
    "this",
    "that",
    "from",
    "by",
    "as",
    "at",
    "it",
    "be",
    "has",
    "have",
    "had",
    "not",
    "but"
}


def normalize_text(
    text: str
) -> str:

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def tokenize(
    text: str
) -> set:

    words = normalize_text(text).split()

    return {
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 2
    }


def local_similarity(
    text1: str,
    text2: str
) -> float:

    a = tokenize(text1)

    b = tokenize(text2)

    if not a or not b:

        return 0.0

    intersection = a.intersection(b)

    union = a.union(b)

    if not union:

        return 0.0

    return len(intersection) / len(union)


# ============================================================
# INCIDENT FINGERPRINTS
# ============================================================

FINGERPRINTS = {

    "DATABASE": [
        "database",
        "db",
        "mysql",
        "postgres",
        "postgresql",
        "sql",
        "connection pool",
        "connection timeout"
    ],

    "TIMEOUT": [
        "timeout",
        "timed out",
        "request timeout",
        "connection timeout"
    ],

    "REDIS": [
        "redis",
        "cache"
    ],

    "DEPLOYMENT": [
        "deployment",
        "deploy",
        "release",
        "latest deployment",
        "new version"
    ],

    "MEMORY": [
        "memory",
        "out of memory",
        "oom",
        "heap"
    ],

    "CPU": [
        "cpu",
        "high cpu",
        "processor"
    ],

    "NETWORK": [
        "network",
        "connection refused",
        "dns",
        "latency"
    ],

    "QUEUE": [
        "queue",
        "consumer",
        "kafka",
        "rabbitmq",
        "processing delayed"
    ],

    "AUTH": [
        "authentication",
        "login",
        "token",
        "401",
        "403",
        "unauthorized",
        "jwt"
    ],

    "PAYMENT": [
        "payment",
        "transaction",
        "charged",
        "billing"
    ],

    "BOOKING": [
        "booking",
        "ticket",
        "reservation",
        "confirmation"
    ]
}


def get_fingerprints(
    text: str
) -> set:

    text = normalize_text(text)

    result = set()

    for category, keywords in FINGERPRINTS.items():

        for keyword in keywords:

            if normalize_text(keyword) in text:

                result.add(category)

                break

    return result


# ============================================================
# HINDSIGHT INITIALIZATION
# ============================================================

def initialize_hindsight():

    global hindsight_client
    global hindsight_connected

    if not HINDSIGHT_AVAILABLE:

        hindsight_connected = False

        return False

    try:

        kwargs = {
            "base_url": HINDSIGHT_BASE_URL,
            "timeout": 10.0
        }

        if HINDSIGHT_API_KEY:

            kwargs["api_key"] = HINDSIGHT_API_KEY

        hindsight_client = Hindsight(
            **kwargs
        )

        # Create memory bank.
        # If it already exists, Hindsight may return an error.
        # We simply continue because the bank is already usable.
        try:

            hindsight_client.create_bank(
                bank_id=HINDSIGHT_BANK_ID,
                name="RE:ACT Incident Memory"
            )

        except Exception:

            pass

        # Test the connection
        try:

            hindsight_client.list_memories(
                bank_id=HINDSIGHT_BANK_ID,
                limit=1
            )

        except Exception:

            # Some configurations may not allow this operation.
            # The client can still be considered configured.
            pass

        hindsight_connected = True

        return True

    except Exception as error:

        print(
            "Hindsight connection failed:",
            error
        )

        hindsight_client = None

        hindsight_connected = False

        return False


# ============================================================
# INITIALIZE RE:ACT
# ============================================================

def initialize_react():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not DATA_FILE.exists():

        save_local_incidents([])

    initialize_hindsight()

    memory_state["initialized"] = True

    memory_state["hindsight_connected"] = (
        hindsight_connected
    )

    memory_state["last_updated"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


# ============================================================
# BUILD MEMORY CONTENT
# ============================================================

def incident_to_memory_text(
    incident: Incident,
    incident_id: str
) -> str:

    return f"""
RE:ACT INCIDENT MEMORY

Incident ID:
{incident_id}

Service:
{incident.service}

Severity:
{incident.severity}

Title:
{incident.title}

Symptoms:
{incident.symptoms}

Logs:
{incident.logs}

Root Cause:
{incident.root_cause}

Attempted Actions:
{incident.attempted_actions}

Failed Actions:
{incident.failed_actions}

Successful Fix:
{incident.successful_fix}

Resolution Time:
{incident.resolution_minutes} minutes

Recent Change:
{incident.recent_change}

This is a resolved technical incident retained by RE:ACT
for future incident investigation.
""".strip()


# ============================================================
# RETAIN MEMORY IN HINDSIGHT
# ============================================================

def retain_in_hindsight(
    incident: Incident,
    incident_id: str
):

    if not hindsight_connected:
        return False

    if hindsight_client is None:
        return False

    try:

        content = incident_to_memory_text(
            incident,
            incident_id
        )

        hindsight_client.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=content,
            context=(
                "RE:ACT technical incident response "
                "and historical troubleshooting memory."
            ),
            document_id=incident_id
        )

        return True

    except Exception as error:

        print(
            "Hindsight retain failed:",
            error
        )

        return False


# ============================================================
# RECALL FROM HINDSIGHT
# ============================================================

def recall_from_hindsight(
    incident: Incident
):

    if not hindsight_connected:
        return []

    if hindsight_client is None:
        return []

    try:

        query = f"""
Find previous technical incidents similar to this incident.

Service:
{incident.service}

Title:
{incident.title}

Symptoms:
{incident.symptoms}

Logs:
{incident.logs}

Recent Change:
{incident.recent_change}

Find previous incidents with similar:
- symptoms
- logs
- service failures
- root causes
- successful fixes
- failed troubleshooting actions
""".strip()

        response = hindsight_client.recall(
            bank_id=HINDSIGHT_BANK_ID,
            query=query,
            max_tokens=4096,
            budget="mid"
        )

        results = []

        if hasattr(response, "results"):

            for item in response.results:

                text = getattr(
                    item,
                    "text",
                    ""
                )

                if text:

                    results.append({
                        "text": text,
                        "type": getattr(
                            item,
                            "type",
                            "memory"
                        )
                    })

        return results

    except Exception as error:

        print(
            "Hindsight recall failed:",
            error
        )

        return []


# ============================================================
# STORE INCIDENT
# ============================================================

def store_incident(
    incident: Incident
):

    initialize_react()

    incidents = load_local_incidents()

    incident_id = (
        "INC-" +
        uuid.uuid4().hex[:8].upper()
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    data = incident.model_dump()

    data["id"] = incident_id

    data["created_at"] = now

    data["updated_at"] = now

    combined_text = " ".join([
        incident.service,
        incident.title,
        incident.symptoms,
        incident.logs,
        incident.root_cause,
        incident.successful_fix,
        incident.failed_actions,
        incident.recent_change
    ])

    data["fingerprints"] = list(
        get_fingerprints(combined_text)
    )

    # --------------------------------------------------------
    # Local memory
    # --------------------------------------------------------

    incidents.append(data)

    save_local_incidents(
        incidents
    )

    # --------------------------------------------------------
    # Hindsight memory
    # --------------------------------------------------------

    hindsight_stored = retain_in_hindsight(
        incident,
        incident_id
    )

    data["hindsight_stored"] = (
        hindsight_stored
    )

    memory_state["last_updated"] = now

    return data


# ============================================================
# ADD DEMO INCIDENTS
# ============================================================

def add_demo_incidents():

    initialize_react()

    existing = load_local_incidents()

    existing_titles = {
        item.get("title")
        for item in existing
    }

    added = []

    for demo in DEMO_INCIDENTS:

        if demo["title"] in existing_titles:

            continue

        incident = Incident(
            **demo
        )

        stored = store_incident(
            incident
        )

        added.append(
            stored
        )

    return added


# ============================================================
# LOCAL HISTORICAL MATCH
# ============================================================

def find_local_match(
    current: Incident
):

    incidents = load_local_incidents()

    if not incidents:

        return None

    current_text = " ".join([
        current.service,
        current.title,
        current.symptoms,
        current.logs,
        current.recent_change
    ])

    current_fingerprints = get_fingerprints(
        current_text
    )

    candidates = []

    for old in incidents:

        old_text = " ".join([
            old.get("service", ""),
            old.get("title", ""),
            old.get("symptoms", ""),
            old.get("logs", ""),
            old.get("root_cause", ""),
            old.get("recent_change", "")
        ])

        text_score = local_similarity(
            current_text,
            old_text
        )

        old_fingerprints = set(
            old.get(
                "fingerprints",
                []
            )
        )

        fingerprint_score = 0

        if current_fingerprints and old_fingerprints:

            common = (
                current_fingerprints
                .intersection(
                    old_fingerprints
                )
            )

            union = (
                current_fingerprints
                .union(
                    old_fingerprints
                )
            )

            if union:

                fingerprint_score = (
                    len(common) /
                    len(union)
                )

        service_score = 0

        if normalize_text(
            current.service
        ) == normalize_text(
            old.get(
                "service",
                ""
            )
        ):

            service_score = 1

        score = (
            text_score * 0.60
            +
            fingerprint_score * 0.25
            +
            service_score * 0.15
        )

        candidates.append({
            "incident": old,
            "score": score
        })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[0]


# ============================================================
# BUILD RECOMMENDATIONS
# ============================================================

def build_recommendations(
    incident: Incident,
    historical: Optional[dict]
):

    recommendations = []

    if historical:

        if historical.get(
            "successful_fix"
        ):

            recommendations.append(
                "Previous successful fix: "
                + historical[
                    "successful_fix"
                ]
            )

        recommendations.append(
            "Compare current conditions with "
            "the previous incident."
        )

        recommendations.append(
            "Verify the highest-signal dependency "
            "before making changes."
        )

        recommendations.append(
            "Check whether the recent deployment "
            "or configuration change is related."
        )

        fingerprints = set(
            historical.get(
                "fingerprints",
                []
            )
        )

        if "DATABASE" in fingerprints:

            recommendations.append(
                "Check database connection pool usage "
                "and active connections."
            )

        if "QUEUE" in fingerprints:

            recommendations.append(
                "Check queue processing, consumers "
                "and retry status."
            )

        if "AUTH" in fingerprints:

            recommendations.append(
                "Verify authentication tokens and "
                "signing configuration."
            )

        if "REDIS" in fingerprints:

            recommendations.append(
                "Check Redis connection pool and "
                "cache availability."
            )

    else:

        recommendations.extend([
            "Inspect the highest-signal error in the logs.",
            "Compare the incident with recent deployments.",
            "Check the affected service dependencies.",
            "Retain the final resolution in Hindsight."
        ])

    return recommendations


# ============================================================
# BUILD AVOID LIST
# ============================================================

def build_avoid(
    historical: Optional[dict]
):

    if not historical:

        return [
            "No previous failed action is available yet."
        ]

    failed = historical.get(
        "failed_actions",
        ""
    )

    if failed:

        return [
            failed
        ]

    return [
        "No failed action was recorded "
        "for this historical incident."
    ]


# ============================================================
# EXTRACT USEFUL INFO FROM HINDSIGHT
# ============================================================

def extract_hindsight_actions(
    hindsight_results
):

    successful = []

    failed = []

    insights = []

    for result in hindsight_results:

        text = result.get(
            "text",
            ""
        )

        lower = text.lower()

        if (
            "successful fix" in lower
            or "worked" in lower
            or "resolved" in lower
        ):

            successful.append(
                text
            )

        elif (
            "failed" in lower
            or "did not resolve" in lower
            or "didn't resolve" in lower
        ):

            failed.append(
                text
            )

        else:

            insights.append(
                text
            )

    return {
        "successful": successful,
        "failed": failed,
        "insights": insights
    }


# ============================================================
# STATUS
# ============================================================

@app.get(
    "/api/status"
)
async def get_status():

    initialize_react()

    incidents = load_local_incidents()

    return {
        "status": "online",

        "service": "RE:ACT",

        "initialized": True,

        "memory_initialized": True,

        "hindsight_available": HINDSIGHT_AVAILABLE,

        "hindsight_connected": hindsight_connected,

        "hindsight_status": (
            "connected"
            if hindsight_connected
            else "fallback"
        ),

        "hindsight_bank": HINDSIGHT_BANK_ID,

        "stored_incidents": len(
            incidents
        ),

        "incident_count": len(
            incidents
        ),

        "memory_layer": (
            "Hindsight + Local Fallback"
            if hindsight_connected
            else "Local Fallback"
        ),

        "message": (
            "RE:ACT memory layer is ready."
        )
    }


# ============================================================
# GET INCIDENT HISTORY
# ============================================================

@app.get(
    "/api/incidents"
)
async def get_incidents():

    initialize_react()

    incidents = load_local_incidents()

    return {
        "success": True,

        "count": len(
            incidents
        ),

        "incidents": incidents,

        "memory_layer": (
            "Hindsight"
            if hindsight_connected
            else "Local"
        )
    }


# ============================================================
# ADD DEMO INCIDENT
# ============================================================

@app.post(
    "/api/seed"
)
async def seed_demo():

    initialize_react()

    added = add_demo_incidents()

    incidents = load_local_incidents()

    return {
        "success": True,

        "message": (
            f"{len(added)} demo incident(s) added."
            if added
            else
            "Demo incidents already exist."
        ),

        "added": added,

        "added_count": len(
            added
        ),

        "count": len(
            incidents
        ),

        "incidents": incidents,

        "hindsight_connected": (
            hindsight_connected
        )
    }


# ============================================================
# RESET LOCAL MEMORY
# ============================================================

@app.post(
    "/api/reset"
)
async def reset_memory():

    global memory_state

    # Clear local memory
    save_local_incidents([])

    now = datetime.now(
        timezone.utc
    ).isoformat()

    memory_state = {
        "initialized": True,
        "hindsight_connected": (
            hindsight_connected
        ),
        "last_updated": now
    }

    return {
        "success": True,

        "message": (
            "RE:ACT local memory has been reset."
        ),

        "count": 0,

        "incidents": [],

        "hindsight_connected": (
            hindsight_connected
        ),

        "note": (
            "Hindsight memories are persistent and "
            "are not deleted by this local reset."
        )
    }


# ============================================================
# CREATE CUSTOM INCIDENT
# ============================================================

@app.post(
    "/api/incidents"
)
async def create_incident(
    incident: Incident
):

    stored = store_incident(
        incident
    )

    return {
        "success": True,

        "message": (
            "Incident stored successfully."
        ),

        "incident": stored,

        "hindsight_stored": (
            stored.get(
                "hindsight_stored",
                False
            )
        )
    }


# ============================================================
# ANALYZE INCIDENT
# ============================================================

@app.post(
    "/api/analyze"
)
async def analyze_incident(
    incident: Incident
):

    initialize_react()

    # --------------------------------------------------------
    # FIRST: RECALL FROM HINDSIGHT
    # --------------------------------------------------------

    hindsight_results = (
        recall_from_hindsight(
            incident
        )
    )

    hindsight_actions = (
        extract_hindsight_actions(
            hindsight_results
        )
    )

    # --------------------------------------------------------
    # SECOND: LOCAL FALLBACK MATCH
    # --------------------------------------------------------

    local_match = find_local_match(
        incident
    )

    historical = None
    local_score = 0.0

    if local_match:

        historical = (
            local_match["incident"]
        )

        local_score = (
            local_match["score"]
        )

    # --------------------------------------------------------
    # HINDSIGHT FOUND SOMETHING
    # --------------------------------------------------------

    hindsight_found = (
        len(hindsight_results) > 0
    )

    # --------------------------------------------------------
    # DETERMINE MATCH SCORE
    # --------------------------------------------------------

    if local_score > 0:

        percentage = round(
            max(
                0,
                min(
                    local_score,
                    1
                )
            ) * 100
        )

    elif hindsight_found:

        # Hindsight found relevant memory,
        # but exact similarity percentage is not
        # exposed by every SDK response.
        percentage = 85

    else:

        percentage = 0

    # --------------------------------------------------------
    # MATCH LABEL
    # --------------------------------------------------------

    if percentage >= 90:

        label = "Historical match found"

    elif percentage >= 70:

        label = "Strong historical match"

    elif percentage >= 50:

        label = "Possible historical match"

    elif percentage >= 30:

        label = "Weak historical similarity"

    else:

        label = "No strong historical match"

    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = build_recommendations(
        incident,
        historical
    )

    # Add Hindsight-specific recommendation
    if hindsight_found:

        recommendations.insert(
            0,
            "Hindsight recalled previous incident experience "
            "relevant to the current investigation."
        )

    # --------------------------------------------------------
    # AVOID
    # --------------------------------------------------------

    avoid = build_avoid(
        historical
    )

    # Add Hindsight failed memories
    if hindsight_actions["failed"]:

        for item in hindsight_actions["failed"][:2]:

            if item not in avoid:

                avoid.append(
                    "Hindsight memory: " +
                    item
                )

    # --------------------------------------------------------
    # SUCCESSFUL FIX
    # --------------------------------------------------------

    successful_fix = ""

    if historical:

        successful_fix = historical.get(
            "successful_fix",
            ""
        )

    # If local memory does not have one,
    # return Hindsight result.
    if (
        not successful_fix
        and hindsight_actions["successful"]
    ):

        successful_fix = (
            hindsight_actions[
                "successful"
            ][0]
        )

    # --------------------------------------------------------
    # ROOT CAUSE
    # --------------------------------------------------------

    root_cause = ""

    if historical:

        root_cause = historical.get(
            "root_cause",
            ""
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "match_found": (
            percentage >= 30
        ),

        "historical_match": (
            percentage >= 30
        ),

        "match_score": round(
            local_score,
            3
        ),

        "match_percentage": percentage,

        "match": f"{percentage}%",

        "match_label": label,

        "message": (
            "Previous experience changes today's investigation."
            if percentage >= 30
            else
            "No strong historical match was found."
        ),

        # ----------------------------------------------------
        # HINDSIGHT
        # ----------------------------------------------------

        "hindsight": {

            "enabled": HINDSIGHT_AVAILABLE,

            "connected": hindsight_connected,

            "recalled": hindsight_found,

            "bank_id": HINDSIGHT_BANK_ID,

            "results": hindsight_results
        },

        "hindsight_connected": (
            hindsight_connected
        ),

        "hindsight_recalled": (
            hindsight_found
        ),

        # ----------------------------------------------------
        # HISTORICAL INCIDENT
        # ----------------------------------------------------

        "historical_incident": historical,

        "previous_successful_fix": (
            successful_fix
        ),

        "successful_fix": (
            successful_fix
        ),

        "failed_actions": (
            historical.get(
                "failed_actions",
                ""
            )
            if historical
            else
            (
                hindsight_actions[
                    "failed"
                ][0]
                if hindsight_actions["failed"]
                else ""
            )
        ),

        "root_cause": root_cause,

        "recommendations": recommendations,

        "avoid": avoid,

        "hindsight_insights": (
            hindsight_actions[
                "insights"
            ]
        ),

        "fingerprints": list(
            get_fingerprints(
                " ".join([
                    incident.service,
                    incident.title,
                    incident.symptoms,
                    incident.logs,
                    incident.recent_change
                ])
            )
        )
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home():

    index_file = (
        STATIC_DIR /
        "index.html"
    )

    if not index_file.exists():

        return HTMLResponse(
            content="""
            <h1>RE:ACT</h1>
            <p>
                static/index.html was not found.
            </p>
            """,
            status_code=404
        )

    return HTMLResponse(
        content=index_file.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(
        directory=str(
            STATIC_DIR
        )
    ),
    name="static"
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event(
    "startup"
)
async def startup_event():

    initialize_react()

    print()
    print("=" * 65)
    print(
        "        RE:ACT — AI INCIDENT COMMAND CENTER"
    )
    print("=" * 65)

    print(
        "Memory initialized : YES"
    )

    print(
        "Hindsight installed:",
        "YES" if HINDSIGHT_AVAILABLE else "NO"
    )

    print(
        "Hindsight connected:",
        "YES" if hindsight_connected else "NO"
    )

    print(
        "Hindsight bank     :",
        HINDSIGHT_BANK_ID
    )

    print(
        "Local incidents    :",
        len(
            load_local_incidents()
        )
    )

    print(
        "API                : "
        "http://127.0.0.1:8001"
    )

    print("=" * 65)
    print()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )