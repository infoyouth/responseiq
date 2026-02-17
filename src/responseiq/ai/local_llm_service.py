"""
Local Mock LLM Service for ResponseIQ Testing & Development

Provides a lightweight, deterministic AI analysis service that mimics OpenAI
responses without requiring external API keys or internet connectivity.
"""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Optional

from responseiq.utils.logger import logger


class LocalMockLLM:
    """
    Local mock LLM that provides deterministic, high-quality incident analysis.

    Features:
    - Pattern-based analysis for common incident types
    - Deterministic responses based on input content
    - Realistic confidence scoring
    - Zero external dependencies
    """

    def __init__(self):
        """Initialize the mock LLM with predefined analysis patterns."""
        self.analysis_patterns = self._build_analysis_patterns()
        logger.info("🤖 LocalMockLLM initialized - Zero dependency AI analysis ready")

    def _build_analysis_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build comprehensive patterns for incident analysis."""
        return {
            # Critical/panic errors (highest priority)
            "critical_error": {
                "patterns": [
                    r"panic",
                    r"critical.*failure",
                    r"critical.*error",
                    r"fatal.*error",
                    r"system.*crash",
                    r"kernel.*panic",
                    r"crashloop",
                    r"crash.*loop",
                    r"restart.*loop",
                ],
                "severity": "high",
                "base_response": {
                    "title": "Critical System Error",
                    "severity": "high",
                    "description": "Critical system failure requiring immediate attention",
                    "remediation": (
                        "1. Investigate system logs immediately\n"
                        "2. Check for hardware or kernel issues\n"
                        "3. Review recent changes that may have caused instability\n"
                        "4. Consider emergency rollback if recent deployment"
                    ),
                    "confidence": 0.90,
                    "rationale": "Critical error patterns detected indicating severe system issues",
                    "affected_files": ["system", "kernel", "core"],
                    "proposed_changes": [
                        {"type": "emergency_response", "description": "Immediate investigation and potential rollback"},
                        {"type": "monitoring", "description": "Enhanced monitoring for system stability"},
                    ],
                },
            },
            # Network and connectivity issues
            "connection_error": {
                "patterns": [
                    r"connection.*refused",
                    r"connection.*timeout",
                    r"httpsconnectionpool.*max retries exceeded",
                    r"network.*unreachable",
                    r"dns.*resolution.*failed",
                ],
                "severity": "high",
                "base_response": {
                    "title": "Network Connectivity Issue",
                    "severity": "high",
                    "description": "Service cannot establish network connections to external endpoints",
                    "remediation": (
                        "1. Verify network connectivity and DNS resolution\n"
                        "2. Check firewall rules and security groups\n"
                        "3. Implement connection retry logic with exponential backoff\n"
                        "4. Add health checks for upstream services"
                    ),
                    "confidence": 0.85,
                    "rationale": "Network connectivity patterns detected in incident logs",
                    "affected_files": ["networking", "config", "services"],
                    "proposed_changes": [
                        {"type": "retry_logic", "description": "Add exponential backoff for failed connections"},
                        {"type": "health_check", "description": "Implement upstream service health monitoring"},
                    ],
                },
            },
            # File system issues
            "file_error": {
                "patterns": [
                    r"filenotfounderror",
                    r"no such file or directory",
                    r"permission denied",
                    r"disk.*full",
                    r"readonly.*filesystem",
                ],
                "severity": "medium",
                "base_response": {
                    "title": "File System Access Issue",
                    "severity": "medium",
                    "description": "Application cannot access required files or directories",
                    "remediation": (
                        "1. Verify file paths and permissions are correct\n"
                        "2. Ensure sufficient disk space is available\n"
                        "3. Add proper error handling for file operations\n"
                        "4. Implement fallback mechanisms for missing configs"
                    ),
                    "confidence": 0.80,
                    "rationale": "File system access patterns identified in logs",
                    "affected_files": ["file_handlers", "config", "storage"],
                    "proposed_changes": [
                        {"type": "error_handling", "description": "Add robust file operation error handling"},
                        {"type": "fallback", "description": "Implement config fallback mechanisms"},
                    ],
                },
            },
            # Database and data issues
            "database_error": {
                "patterns": [
                    r"database.*connection.*failed",
                    r"sql.*syntax.*error",
                    r"deadlock.*detected",
                    r"table.*doesn.*exist",
                    r"connection.*pool.*exhausted",
                ],
                "severity": "high",
                "base_response": {
                    "title": "Database Connectivity/Query Issue",
                    "severity": "high",
                    "description": "Database operations are failing or performing poorly",
                    "remediation": (
                        "1. Check database connectivity and credentials\n"
                        "2. Review SQL queries for syntax errors\n"
                        "3. Optimize queries and add proper indexing\n"
                        "4. Implement connection pooling and retry logic"
                    ),
                    "confidence": 0.88,
                    "rationale": "Database operation patterns identified in incident logs",
                    "affected_files": ["database", "models", "queries"],
                    "proposed_changes": [
                        {"type": "query_optimization", "description": "Optimize slow database queries"},
                        {"type": "connection_pool", "description": "Implement robust database connection pooling"},
                    ],
                },
            },
            # Memory and performance issues
            "memory_error": {
                "patterns": [
                    r"out of memory",
                    r"memory.*exhausted",
                    r"heap.*overflow",
                    r"cpu.*high.*usage",
                    r"timeout.*exceeded",
                    r"oomkilled",
                    r"oom.*killed",
                    r"killed.*oom",
                ],
                "severity": "high",
                "base_response": {
                    "title": "Memory/Resource Exhaustion Issue",
                    "severity": "high",
                    "description": (
                        "System resources (memory/CPU) are being exhausted, potentially causing container restarts"
                    ),
                    "remediation": (
                        "1. Increase memory limits for affected containers\n"
                        "2. Profile application for memory leaks\n"
                        "3. Optimize resource-intensive operations\n"
                        "4. Implement proper resource cleanup\n"
                        "5. Add memory monitoring and alerting"
                    ),
                    "confidence": 0.85,
                    "rationale": "Memory exhaustion patterns detected in system/container logs",
                    "affected_files": ["deployment", "performance", "cleanup", "monitoring"],
                    "proposed_changes": [
                        {"type": "resource_limits", "description": "Increase container memory limits"},
                        {"type": "optimization", "description": "Optimize memory usage and implement cleanup"},
                        {"type": "monitoring", "description": "Add resource usage monitoring"},
                    ],
                },
            },
            # Authentication and authorization
            "auth_error": {
                "patterns": [
                    r"unauthorized",
                    r"access.*denied",
                    r"authentication.*failed",
                    r"invalid.*credentials",
                    r"token.*expired",
                ],
                "severity": "medium",
                "base_response": {
                    "title": "Authentication/Authorization Issue",
                    "severity": "medium",
                    "description": "Authentication or authorization mechanisms are failing",
                    "remediation": (
                        "1. Verify credentials and token validity\n"
                        "2. Check authentication service availability\n"
                        "3. Implement proper token refresh logic\n"
                        "4. Add authentication error handling"
                    ),
                    "confidence": 0.75,
                    "rationale": "Authentication/authorization patterns found in access logs",
                    "affected_files": ["auth", "tokens", "middleware"],
                    "proposed_changes": [
                        {"type": "token_refresh", "description": "Implement automatic token refresh mechanism"},
                        {"type": "auth_fallback", "description": "Add authentication fallback strategies"},
                    ],
                },
            },
            # Application errors
            "application_error": {
                "patterns": [
                    r"null.*pointer",
                    r"index.*out.*of.*bounds",
                    r"key.*error",
                    r"attribute.*error",
                    r"value.*error",
                ],
                "severity": "medium",
                "base_response": {
                    "title": "Application Logic Error",
                    "severity": "medium",
                    "description": "Application code is encountering runtime errors",
                    "remediation": (
                        "1. Add proper null checks and validation\n"
                        "2. Implement defensive programming practices\n"
                        "3. Add comprehensive error handling\n"
                        "4. Increase test coverage for edge cases"
                    ),
                    "confidence": 0.78,
                    "rationale": "Application runtime error patterns identified in logs",
                    "affected_files": ["application", "validation", "handlers"],
                    "proposed_changes": [
                        {"type": "validation", "description": "Add robust input validation and null checks"},
                        {"type": "error_handling", "description": "Implement comprehensive error handling"},
                    ],
                },
            },
        }

    async def analyze_incident(self, log_text: str, code_context: str = "") -> Optional[Dict[str, Any]]:
        """
        Analyze incident using pattern matching and deterministic logic.

        Args:
            log_text: The incident log content to analyze
            code_context: Additional source code context (optional)

        Returns:
            Structured analysis result matching OpenAI format
        """
        if not log_text or len(log_text.strip()) < 10:
            logger.warning("🤖 LocalMockLLM: Insufficient log content for analysis")
            return None

        # Normalize text for pattern matching
        normalized_text = log_text.lower()

        # Filter out informational/success messages that shouldn't create incidents
        non_incident_patterns = [
            r"informational:",
            r"completed successfully",
            r"job.*completed",
            r"task.*finished",
            r"startup.*complete",
            r"initialization.*complete",
            r"health.*check.*passed",
            r"backup.*completed",
            r"deployment.*successful",
            r"just.*normal.*log",
            r"normal.*log.*message",
            r"^info:",
            r"^debug:",
            r"^trace:",
            r"status.*ok",
            r"request.*processed",
            r"user.*logged.*in",
            r"connection.*established",
            r"all.*good",
            r"harmless.*info",
            r"this.*is.*harmless",
            r"everything.*ok",
            r"working.*fine",
        ]

        # Check if this is just informational noise
        for pattern in non_incident_patterns:
            if re.search(pattern, normalized_text):
                logger.info("🤖 LocalMockLLM: Skipping informational message, not an incident")
                return None

        # Find matching pattern category
        matched_category = None
        confidence_boost = 0.0

        for category, pattern_data in self.analysis_patterns.items():
            for pattern in pattern_data["patterns"]:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    matched_category = category
                    confidence_boost = 0.05  # Boost confidence for pattern match
                    logger.info(f"🤖 LocalMockLLM: Matched pattern category '{category}' for analysis")
                    break
            if matched_category:
                break

        # Use generic fallback if no specific pattern matches
        if not matched_category:
            matched_category = "application_error"
            logger.info("🤖 LocalMockLLM: Using generic application error analysis")

        # Get base response and customize it
        base_response = self.analysis_patterns[matched_category]["base_response"].copy()

        # Customize response based on input content
        base_response = self._customize_response(base_response, log_text, code_context)

        # Adjust confidence based on content quality
        base_response["confidence"] = min(
            1.0,
            base_response["confidence"] + confidence_boost + self._calculate_content_confidence(log_text, code_context),
        )

        # Add deterministic elements based on content hash (for reproducibility)
        content_hash = self._generate_content_hash(log_text)
        base_response = self._add_deterministic_elements(base_response, content_hash)

        logger.info(f"🤖 LocalMockLLM: Generated analysis with {base_response['confidence']:.2f} confidence")
        return base_response

    def _customize_response(self, response: Dict[str, Any], log_text: str, code_context: str) -> Dict[str, Any]:
        """Customize the base response based on specific log content."""
        # Extract specific details from log text
        if "api" in log_text.lower():
            response["title"] = response["title"].replace("Issue", "API Issue")
        if "database" in log_text.lower() or "sql" in log_text.lower():
            response["title"] = response["title"].replace("Issue", "Database Issue")
        if "timeout" in log_text.lower():
            response["description"] += " - Timeout patterns detected"

        # Add code context insights
        if code_context:
            response["rationale"] += " - Source code context provided for enhanced accuracy"
            response["confidence"] += 0.1  # Boost confidence with code context

        # Extract potential file names or paths from logs
        file_matches = re.findall(
            r"([a-zA-Z_][a-zA-Z0-9_]*\.py|[a-zA-Z_][a-zA-Z0-9_]*\.js|[a-zA-Z_][a-zA-Z0-9_]*\.java)", log_text
        )
        if file_matches:
            response["affected_files"].extend(file_matches[:3])  # Add up to 3 files

        return response

    def _calculate_content_confidence(self, log_text: str, code_context: str) -> float:
        """Calculate confidence boost based on content quality."""
        confidence_boost = 0.0

        # More detailed logs = higher confidence
        if len(log_text) > 200:
            confidence_boost += 0.05
        if len(log_text) > 500:
            confidence_boost += 0.05

        # Stack traces increase confidence
        if "traceback" in log_text.lower() or "stack trace" in log_text.lower():
            confidence_boost += 0.1

        # Specific error messages increase confidence
        if re.search(r"\w+Error:", log_text):
            confidence_boost += 0.08

        # Code context increases confidence
        if code_context and len(code_context) > 100:
            confidence_boost += 0.1

        return min(0.15, confidence_boost)  # Cap the boost

    def _generate_content_hash(self, content: str) -> str:
        """Generate deterministic hash for content-based customization."""
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:8]

    def _add_deterministic_elements(self, response: Dict[str, Any], content_hash: str) -> Dict[str, Any]:
        """Add deterministic elements based on content hash for reproducibility."""
        # Use hash to deterministically vary some response elements
        hash_int = int(content_hash, 16)

        # Slightly vary confidence in a deterministic way
        confidence_variation = (hash_int % 100) / 1000.0  # 0.000 to 0.099
        response["confidence"] = min(1.0, response["confidence"] + confidence_variation)

        # Add timestamp for traceability
        response["analysis_timestamp"] = datetime.now().isoformat()
        response["analysis_method"] = "local_mock_llm"
        response["content_signature"] = content_hash

        return response


# Global instance
local_mock_llm = LocalMockLLM()


async def analyze_with_local_llm(log_text: str, code_context: str = "") -> Optional[Dict[str, Any]]:
    """
    Drop-in replacement for OpenAI analysis using local mock LLM.

    This function provides the same interface as the OpenAI service
    but uses deterministic, pattern-based analysis locally.
    """
    return await local_mock_llm.analyze_incident(log_text, code_context)
