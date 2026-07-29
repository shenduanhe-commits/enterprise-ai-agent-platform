# Enterprise AI Agent Platform (EAAP)

> An enterprise-grade AI Agent platform built with modern AI application architecture.

![Status](https://img.shields.io/badge/status-under%20development-blue)
![Vue](https://img.shields.io/badge/frontend-Vue3-green)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-blue)
![Python](https://img.shields.io/badge/python-3.12+-yellow)

---

# Overview

Enterprise AI Agent Platform (EAAP) is an enterprise-oriented AI Agent platform.

The goal is to build a complete AI application system that supports:

- AI Chat
- Retrieval Augmented Generation (RAG)
- Tool Calling
- Agent Workflow
- Multi-Agent Collaboration
- A2A Communication
- MCP Integration

This project follows real enterprise software development practices.

It includes:

- Product design
- System architecture
- Database design
- API design
- Agent architecture
- Engineering workflow
- Testing
- Deployment

---

# Project Vision

Traditional enterprise software:

```
User
 |
Business System
 |
Database
```

Future AI enterprise applications:

```
User

 |

AI Agent Platform

 |

Knowledge
Business Tools
Enterprise Systems

 |

Automated Workflows
```

EAAP aims to become an AI workspace where employees can communicate with enterprise knowledge and systems through intelligent agents.

---

# Main Features

## AI Assistant

Features:

- Chat conversation
- Streaming response
- Conversation history
- Markdown rendering
- File interaction


---

## Enterprise Knowledge Base

Support:

- Document upload
- Document parsing
- Embedding
- Vector search
- RAG question answering


Supported documents:

- PDF
- Word
- Markdown
- Excel


---

## Agent System

Architecture:

```
                 User

                  |

          Supervisor Agent

                  |

 --------------------------------

 |              |               |

Knowledge    Business      Document

Agent        Agent         Agent

```

---

## Business Integration

Support:

- API integration
- Database query
- Enterprise tools
- External services


---

## Multi-Agent System

Future support:

- Agent collaboration
- Agent communication
- A2A protocol


---

## MCP Integration

Support external capabilities through:

- MCP Client
- MCP Server


---

# Technology Stack

## Frontend

```
Vue 3

TypeScript

Vite

Pinia

Vue Router

Vitest

Playwright

```

---

## Backend

```
Python

FastAPI

SQLAlchemy

PostgreSQL

Redis

```

---

## AI Stack

```
LLM API

OpenAI SDK

RAG

LangGraph

Vector Database

Qdrant

```

---

## Engineering

```
Docker

GitHub Actions

ESLint

Oxlint

Ruff

Pytest

```

---

# Architecture Overview

```
                    Browser

                       |

                    Vue App

                       |

                    FastAPI

                       |

              Agent Orchestration

                       |

        --------------------------------

        |              |               |

    Knowledge      Business       Document

      Agent          Agent          Agent


                       |

              Enterprise Systems

```

---

# Repository Structure

```
enterprise-ai-agent-platform

apps/

├── web

└── api


packages/

├── agent-core

├── rag-core

├── shared

├── ui

└── observer


docs/

docker/

scripts/

tests/

.github/

```

---

# Development Roadmap

## Phase 1
AI Chat Platform

Status:

🚧 Developing


Features:

- Chat UI
- LLM integration
- Streaming
- Conversation


---

## Phase 2

Knowledge Intelligence

Features:

- RAG
- Document processing
- Vector database


---

## Phase 3

Agent Platform

Features:

- LangGraph
- Workflow
- Supervisor Agent


---

## Phase 4

Enterprise Capability

Features:

- Tool Calling
- Business Agent
- Document Agent


---

## Phase 5

Advanced Agent System

Features:

- Multi-Agent
- A2A
- MCP


---

# Engineering Principles

## 1. Product First

Every feature starts from business requirements.

---

## 2. Architecture Driven

Every important decision has documentation.

---

## 3. Production Ready

The project follows enterprise engineering practices.

---

## 4. Continuous Improvement

Every milestone produces:

- Code
- Documentation
- Tests
- Release notes


---

# Learning Goals

Through this project, developers will learn:

## AI Application Development

- LLM integration
- Prompt engineering
- RAG
- Agent architecture


## Software Engineering

- Full-stack development
- System design
- Database design
- API design


## Enterprise Engineering

- Docker
- CI/CD
- Testing
- Monitoring


---

# License

MIT License

---

# Author

Enterprise AI Agent Platform Team
