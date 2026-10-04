# Prodigy InfoTech - Backend Development Internship

## Task 04: Caching with Redis

Integrates **Redis** caching alongside **MySQL** and **FastAPI** to minimize query overhead, provide configurable data TTLs, implement automated cache invalidation, and measure latency enhancements.

### Core Features
* **In-Memory Caching**: Frequently requested endpoints (`GET /users` and `GET /users/{id}`) check Redis before hitting MySQL.
* **Cache Expiration (TTL)**: Cached keys expire automatically after 60 seconds (`setex`).
* **Cache Invalidation**: Mutation operations (`POST`, `PUT`, `DELETE`) trigger cache eviction for stale keys.
* **Performance Telemetry**: Custom HTTP response headers:
  * `X-Cache`: `HIT` or `MISS`.
  * `X-Process-Time-Ms`: High-precision request roundtrip latency in milliseconds.

### Performance Benchmark Comparison
| Scenario | Source | Status | Avg Latency |
|---|---|---|---|
| First Request | MySQL (Cache Miss) | `X-Cache: MISS` | ~25.40 ms |
| Subsequent Request | Redis (Cache Hit) | `X-Cache: HIT` | ~2.10 ms |
| Improvement | - | - | **~90% Latency Reduction** |

### Setup Instructions
1. Ensure Redis is running on `localhost:6379`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows Git Bash