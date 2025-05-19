"""Observability and monitoring module for Azure drift detection.

This module provides integration with popular observability tools and implements
structured logging, metrics collection, and distributed tracing capabilities.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path
import threading
from collections import defaultdict

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Structured logging
import structlog

class ObservabilityManager:
    """Manages observability tools and integrations for the application."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the observability manager.

        Args:
            config: Configuration dictionary containing observability settings
        """
        self.config = config
        self._setup_logging()
        self._setup_metrics()
        self._setup_tracing()
        self._setup_alerting()

    def _setup_logging(self):
        """Configure structured logging with OpenTelemetry integration."""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure OpenTelemetry logging
        LoggingInstrumentor().instrument()

        self.logger = structlog.get_logger()

    def _setup_metrics(self):
        """Configure Prometheus metrics collection."""
        # Drift detection metrics
        self.drift_counter = Counter(
            'drift_detections_total',
            'Total number of drift detections',
            ['severity', 'resource_type']
        )
        self.drift_duration = Histogram(
            'drift_detection_duration_seconds',
            'Time spent detecting drift',
            ['resource_type']
        )
        self.resource_count = Gauge(
            'azure_resources_total',
            'Total number of Azure resources monitored',
            ['resource_type']
        )

        # API metrics
        self.api_requests = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['endpoint', 'method', 'status']
        )
        self.api_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['endpoint', 'method']
        )

        # System metrics
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes'
        )
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )

        # Start Prometheus metrics server
        start_http_server(self.config.get('metrics_port', 9090))

    def _setup_tracing(self):
        """Configure OpenTelemetry distributed tracing."""
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())

        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.config.get('otlp_endpoint', 'localhost:4317'),
            insecure=True
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        self.tracer = trace.get_tracer(__name__)

    def _setup_alerting(self):
        """Configure alerting rules and thresholds."""
        self.alert_thresholds = {
            'high_severity_drift': 5,  # Alert after 5 high severity drifts
            'api_error_rate': 0.1,     # Alert if error rate > 10%
            'memory_usage': 0.9,       # Alert if memory usage > 90%
            'cpu_usage': 0.8,          # Alert if CPU usage > 80%
        }

    def record_drift(self, severity: str, resource_type: str, duration: float):
        """Record drift detection metrics.

        Args:
            severity: Severity level of the drift
            resource_type: Type of resource that drifted
            duration: Time taken to detect drift
        """
        self.drift_counter.labels(severity=severity, resource_type=resource_type).inc()
        self.drift_duration.labels(resource_type=resource_type).observe(duration)

        # Log drift detection
        self.logger.info(
            "drift_detected",
            severity=severity,
            resource_type=resource_type,
            duration=duration
        )

    def record_api_request(self, endpoint: str, method: str, status: int, duration: float):
        """Record API request metrics.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status: Response status code
            duration: Request duration
        """
        self.api_requests.labels(
            endpoint=endpoint,
            method=method,
            status=status
        ).inc()
        self.api_duration.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)

    def update_resource_count(self, resource_type: str, count: int):
        """Update resource count metrics.

        Args:
            resource_type: Type of Azure resource
            count: Number of resources
        """
        self.resource_count.labels(resource_type=resource_type).set(count)

    def update_system_metrics(self, memory_usage: float, cpu_usage: float):
        """Update system resource usage metrics.

        Args:
            memory_usage: Memory usage in bytes
            cpu_usage: CPU usage percentage
        """
        self.memory_usage.set(memory_usage)
        self.cpu_usage.set(cpu_usage)

        # Check for alerts
        if cpu_usage > self.alert_thresholds['cpu_usage']:
            self.logger.warning(
                "high_cpu_usage",
                cpu_usage=cpu_usage,
                threshold=self.alert_thresholds['cpu_usage']
            )

        if memory_usage > self.alert_thresholds['memory_usage']:
            self.logger.warning(
                "high_memory_usage",
                memory_usage=memory_usage,
                threshold=self.alert_thresholds['memory_usage']
            )

    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a new trace span.

        Args:
            name: Name of the span
            attributes: Optional span attributes

        Returns:
            A context manager for the span
        """
        return self.tracer.start_as_current_span(name, attributes=attributes)

    def log_event(self, event: str, **kwargs):
        """Log an event with structured data.

        Args:
            event: Event name
            **kwargs: Additional event data
        """
        self.logger.info(event, **kwargs)

    def log_error(self, error: Exception, **kwargs):
        """Log an error with structured data.

        Args:
            error: Exception to log
            **kwargs: Additional error context
        """
        self.logger.error(
            "error_occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics.

        Returns:
            Dictionary containing metrics summary
        """
        return {
            'drift_detections': {
                'total': self.drift_counter._value.get(),
                'by_severity': {
                    severity: count
                    for severity, count in self.drift_counter._metrics.items()
                }
            },
            'api_requests': {
                'total': self.api_requests._value.get(),
                'by_endpoint': {
                    endpoint: count
                    for endpoint, count in self.api_requests._metrics.items()
                }
            },
            'system': {
                'memory_usage': self.memory_usage._value.get(),
                'cpu_usage': self.cpu_usage._value.get()
            }
        } 