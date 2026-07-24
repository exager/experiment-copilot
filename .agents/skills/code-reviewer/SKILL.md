---
name: code-reviewer
description: Comprehensive code review skill for TypeScript, JavaScript, Python, Go, and other languages. Provides code quality analysis, security vulnerability scanning, performance optimization, best practice checking, and review checklist generation. Use when reviewing code, pull requests, providing code feedback, identifying security or performance bugs, or ensuring quality standards.
---

# Code Reviewer Skill

A comprehensive toolkit and methodology for conducting thorough, actionable, and high-impact code reviews across multiple programming languages.

## When to Use This Skill
Activate or refer to this skill whenever performing:
- **Pull Request / Code Review**: Analyzing new changes or diffs before merging.
- **Security Audit**: Scanning for OWASP vulnerabilities, secret leaks, or insecure input handling.
- **Code Quality Assessment**: Checking readability, maintainability, architectural consistency, and test coverage.
- **Refactoring & Performance Optimization**: Identifying bottlenecks, memory leaks, redundant database/API calls, and unhandled edge cases.

---

## Code Review Workflow

### 1. High-Level Architecture & Intent
- Understand the primary goal of the change set.
- Check if design patterns conform to existing codebase standards.
- Verify separation of concerns and component boundary encapsulation.

### 2. Security & Safety Scan
- **Input Validation & Sanitization**: Ensure untrusted data is sanitized before use in database queries, OS calls, or rendering.
- **Authentication & Authorization**: Verify endpoints enforce proper permissions and identity checks.
- **Secrets Management**: Check that no API keys, credentials, or private tokens are hardcoded.
- **Error Handling**: Ensure exception handling does not leak internal stack traces or database errors to end users.

### 3. Code Quality & Clean Code
- **Naming & Readability**: Clear function, variable, and class names reflecting intent.
- **DRY (Don't Repeat Yourself)**: Flag unnecessary code duplication.
- **KISS (Keep It Simple, Stupid)**: Avoid over-engineering or overly complex nested logic.
- **Type Safety**: Ensure proper type annotations, null/undefined checks, and defensive programming.

### 4. Performance & Scalability
- Check for $O(N^2)$ loops, N+1 query problems, and unindexed database queries.
- Ensure proper resource cleanup (unclosed database connections, streams, event listeners).
- Verify async/await and concurrency safety.

### 5. Testing & Verification
- Check that new/modified logic has corresponding unit or integration tests.
- Ensure edge cases (null inputs, empty arrays, timeout errors) are covered.

---

## Structured Review Feedback Format

When delivering a code review, structure your report as follows:

1. **Executive Summary**: Brief overall assessment (Ready to merge, Changes requested, Needs discussion).
2. **Critical / Blocking Issues (Severity: High)**: Security vulnerabilities, bugs, data corruption risks.
3. **Important Improvements (Severity: Medium)**: Performance bottlenecks, missing error handling, lack of tests.
4. **Suggestions & Nits (Severity: Low)**: Style suggestions, non-critical readability tweaks.
5. **Positive Highlights**: Notable good patterns, elegant solutions, or great tests.

---

## Detailed Guidelines & Checklist

For a detailed multi-language checklist and reference patterns, view [code_review_checklist.md](file:///c:/Users/surbh/OneDrive/Desktop/dtdl/experiment-copilot/.agents/skills/code-reviewer/references/code_review_checklist.md).
