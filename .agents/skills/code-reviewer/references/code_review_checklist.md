# Comprehensive Code Review Checklist & Best Practices

## 1. Security Checklist
- [ ] **No Secrets Hardcoded**: No passwords, private keys, API tokens, or tokens in source code.
- [ ] **Input Sanitization**: SQL injection, XSS, and command injection protections are active.
- [ ] **Authorization Enforcement**: User identity and permission checks exist on every sensitive endpoint.
- [ ] **Safe Serialization**: Avoid unsafe deserialization of untrusted payloads.
- [ ] **CORS & CSRF**: Proper headers and anti-CSRF token verification configured.

## 2. Performance & Concurrency Checklist
- [ ] **No N+1 Queries**: Database queries are batched or eager-loaded where appropriate.
- [ ] **Memory & Resource Leak Prevention**: Streams, database connections, and file handles are closed properly in `finally` blocks or using context managers.
- [ ] **Async & Threading**: Non-blocking I/O used on main loop threads; lock acquisition order avoids deadlocks.
- [ ] **Caching**: High-frequency queries or expensive calculations cached appropriately with eviction strategies.

## 3. Code Style & Maintainability Checklist
- [ ] **Single Responsibility Principle**: Classes and functions focus on a single task.
- [ ] **Function Length**: Functions are short and easy to reason about.
- [ ] **Comments & Documentation**: Complex algorithms have comments explaining *why*, not just *what*.
- [ ] **Error Handling**: Exceptions are caught specifically (avoid bare `except:` or `catch (e)` without rethrowing or logging).

## 4. Testing & Reliability Checklist
- [ ] **Unit Test Coverage**: New functions and branches have unit tests.
- [ ] **Edge Cases Covered**: Zero values, empty collections, boundary limits, and unexpected API responses handled cleanly.
- [ ] **Deterministic Tests**: No reliance on hardcoded time, sleep timers, or non-deterministic test order.
