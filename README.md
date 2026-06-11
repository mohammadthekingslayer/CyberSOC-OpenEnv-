---
title: CyberSOC OpenEnv
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
tags:
  - openenv
  - cybersecurity
  - soc
  - reinforcement-learning
  - security
pinned: false
license: mit
---

# CyberSOC OpenEnv 🛡️

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-success)](https://github.com/huggingface/openenv)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)

## Overview

**CyberSOC OpenEnv** is a production-grade AI training environment for Security Operations Center (SOC) analyst workflows. Built for the OpenEnv competition, it simulates real-world cybersecurity incidents where AI agents must investigate alerts, analyze logs, and execute containment actions to neutralize threats.

### Why This Environment?

- **Real-World Relevance**: Models actual SOC analyst decision-making under pressure
- **Progressive Difficulty**: 3 tasks ranging from Easy (brute force) to Hard (APT investigation)
- **Deterministic Grading**: Reproducible evaluation with clear success criteria
- **Rich Feedback**: Step-by-step rewards guide agent learning
- **Production Ready**: Full Docker support, HuggingFace Spaces deployment

---

## 🎯 Action Space

Agents interact via JSON actions specifying the operation type, target, and reasoning.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | `string` | Yes | One of: `analyze_log`, `block_ip`, `isolate_device`, `mark_safe`, `escalate`, `run_scan`, `correlate_events` |
| `target` | `string` | Yes | Specific entity (IP address, hostname, file hash, log ID) |
| `reasoning` | `string` | No | Agent's explanation for the action |

**Example Action:**
```json
{
  "action_type": "block_ip",
  "target": "203.0.113.45",
  "reasoning": "IP performed 50+ failed SSH attempts - confirmed brute force attack"
}
```

---

## 📊 Observation Space

After each action, the environment returns structured feedback:

| Field | Type | Description |
|-------|------|-------------|
| `logs` | `list[str]` | New raw logs relevant to the investigation |
| `alerts` | `list[str]` | High-priority SIEM alerts |
| `network_status` | `dict` | Current state of network assets |
| `threat_level` | `string` | Aggregate threat level: `low`, `medium`, `high`, `critical` |
| `message` | `string` | Direct feedback on the action result |
| `done` | `boolean` | Episode termination flag |
| `reward` | `float` | Numeric reward for the action taken |

---

## 📋 Tasks

### Task 1: Brute Force Detection (Easy)
**Objective**: Identify and block an external IP conducting SSH brute force attacks

**Expected Actions**:
1. Analyze logs for suspicious IP (10.0.0.55)
2. Block the malicious IP at firewall
3. Escalate to security team

**Pass Threshold**: 70% (0.7) | **Max Steps**: 20

---

### Task 2: Malware Containment (Medium)
**Objective**: Detect malware infection, identify C2 communication, and isolate compromised systems

**Expected Actions**:
1. Investigate malicious executable (invoice.exe)
2. Analyze C2 server communications (198.51.100.42)
3. Block C2 IP at perimeter
4. Isolate infected workstation (WS-042)

**Pass Threshold**: 70% (0.7) | **Max Steps**: 30

---

### Task 3: APT Investigation (Hard)
**Objective**: Uncover multi-stage Advanced Persistent Threat with phishing, lateral movement, and data exfiltration

**Expected Actions**:
1. Investigate phishing delivery (weaponized PDF)
2. Trace lateral movement to Domain Controller (DC-01)
3. Contain infection source (WS-042)
4. Eradicate threats on tier-0 assets
5. Escalate to incident response
6. Initiate recovery procedures

**Pass Threshold**: 70% (0.7) | **Max Steps**: 50

---

## 🎁 Reward Function

The reward engine provides dense signals based on action quality and task difficulty:

### Base Rewards (scaled by difficulty)
- **Analyze Log**: 10 points (×1.5 if within first 5 steps)
- **Block IP / Isolate Device**: 15 points
- **Escalate**: 5 points
- **Run Scan**: 10 points
- **Correlate Events**: 10 points

### Task Difficulty Multipliers
- Easy (Task 1): 1.0×
- Medium (Task 2): 1.2×
- Hard (Task 3): 1.5×

### Penalties
- **Duplicate Actions**: -50% per repetition
- **Acting Without Investigation**: -70% if blocking/isolating on step 0
- **False Safety Declarations**: -5 points if marking safe without analysis

---

## 🔐 Environment Variables (Required by Round 1)

Set these in Hugging Face Space **Settings → Variables and secrets**:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Optional local compatibility:
- `API_KEY` (if set, works as alias in `inference.py`)

Do **not** commit `.env` with real keys.

---

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://huggingface.co/spaces/shaik347/cyber-soc-env
cd cyber-soc-env

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export API_KEY="your-api-key"  # Gemini/OpenAI key
export API_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
export MODEL_NAME="gemini-2.0-flash-exp"

# Run baseline inference
PYTHONPATH=src python3 inference.py
```

### Docker Deployment

```bash
# Build image
docker build -t cyber-soc-env .

# Run container
docker run -p 7860:7860 cyber-soc-env
```

### HuggingFace Spaces
The environment auto-deploys to HF Spaces. Access the API at:
```
https://shaik347-cyber-soc-env.hf.space/docs
```

---

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Landing page with task descriptions |
| `POST` | `/reset` | Reset environment to initial state |
| `POST` | `/step` | Execute an action |
| `GET` | `/state` | Get current environment state |
| `GET` | `/tasks` | List all available tasks |
| `GET` | `/grader` | Get episode score (0.0-1.0) |
| `GET` | `/baseline` | Run full benchmark on all tasks |
| `GET` | `/verify` | System health and compliance check |
| `GET` | `/docs` | Interactive API documentation |

---

## 📈 Baseline Scores

Verified baseline performance using `inference.py` with `gemini-2.0-flash-exp`:

| Task | Score | Status | Notes |
|------|-------|--------|-------|
| Task 1 | 0.850+ | ✅ PASS | Reliable brute force detection |
| Task 2 | 0.720+ | ✅ PASS | Good malware containment |
| Task 3 | 0.700+ | ✅ PASS | Challenging APT investigation |

*Scores may vary based on LLM model and temperature settings*

---

## 🏗️ Project Structure

```
cyber-soc-env/
├── src/cyber_soc_env/
│   ├── api/              # FastAPI application
│   ├── env/              # Core environment logic
│   │   ├── environment.py
│   │   ├── reward_engine.py
│   │   └── state_manager.py
│   ├── graders/          # Task graders
│   │   ├── grader_task1.py
│   │   ├── grader_task2.py
│   │   └── grader_task3.py
│   ├── tasks/            # Task definitions
│   └── models.py         # Pydantic data models
├── inference.py          # Baseline agent script
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
├── openenv.yaml          # OpenEnv metadata
└── README.md            # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` or `HF_TOKEN` | Yes | - | API key for LLM provider |
| `API_BASE_URL` | No | Gemini endpoint | LLM API base URL |
| `MODEL_NAME` | No | `gemini-2.0-flash-exp` | Model identifier |
| `CYBER_SOC_BENCHMARK` | No | `cyber-soc-env` | Benchmark name for logging |

---

## 🧪 Testing & Validation

### Run OpenEnv Validation
```bash
openenv validate
```

### Run Unit Tests
```bash
PYTHONPATH=src pytest tests/
```

### Manual API Testing
```bash
# Start server
uvicorn cyber_soc_env.api.app:app --reload

# Test reset
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{"task_id": "task1"}'

# Test step
curl -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{
  "action_type": "analyze_log",
  "target": "10.0.0.55",
  "reasoning": "Investigating suspicious IP"
}'
```

---

## 📜 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request for:
- New task scenarios
- Improved grading logic
- Performance optimizations
- Documentation improvements

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/shaik347/cyber-soc-env/issues)
- **Discussions**: [HuggingFace Community](https://huggingface.co/spaces/shaik347/cyber-soc-env/discussions)
- **Email**: shaik347@example.com

---

## 🙏 Acknowledgments

Built for the **OpenEnv Competition** by HuggingFace and Meta.

- OpenEnv Framework: [https://github.com/huggingface/openenv](https://github.com/huggingface/openenv)
- Competition Details: [OpenEnv Competition Page](https://huggingface.co/openenv)

---

**Made with ❤️ for the AI Security Community**
