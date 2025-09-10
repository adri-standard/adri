"""
Cost Control Utilities for Examples Testing

Provides rate limiting and cost estimation for API-based tests.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class APICallRecord:
    """Record of an API call for cost tracking."""

    timestamp: datetime
    framework: str
    test_name: str
    estimated_cost: float
    tokens_used: Optional[int] = None
    success: bool = True


@dataclass
class CostController:
    """Controls API usage costs during testing."""

    max_calls_per_framework: int = 5
    max_total_calls: int = 35  # 7 frameworks * 5 calls
    max_estimated_cost: float = 0.50  # $0.50 total limit
    rate_limit_seconds: float = 1.0  # Min time between calls

    # Internal tracking
    call_records: List[APICallRecord] = field(default_factory=list)
    last_call_time: Optional[datetime] = None

    def can_make_call(
        self, framework: str, test_name: str, estimated_cost: float = 0.01
    ) -> tuple[bool, str]:
        """
        Check if an API call can be made within cost limits.

        Args:
            framework: Name of the framework being tested
            test_name: Name of the specific test
            estimated_cost: Estimated cost of the API call

        Returns:
            (can_proceed, reason) - True if call allowed, False with reason if blocked
        """
        # Check total call limit
        if len(self.call_records) >= self.max_total_calls:
            return False, f"Maximum total calls ({self.max_total_calls}) reached"

        # Check framework-specific limit
        framework_calls = [r for r in self.call_records if r.framework == framework]
        if len(framework_calls) >= self.max_calls_per_framework:
            return (
                False,
                f"Maximum calls for {framework} ({self.max_calls_per_framework}) reached",
            )

        # Check total cost limit
        total_cost = sum(r.estimated_cost for r in self.call_records)
        if total_cost + estimated_cost > self.max_estimated_cost:
            return (
                False,
                f"Cost limit (${self.max_estimated_cost:.2f}) would be exceeded",
            )

        # Check rate limiting
        if self.last_call_time:
            time_since_last = datetime.now() - self.last_call_time
            if time_since_last.total_seconds() < self.rate_limit_seconds:
                wait_time = self.rate_limit_seconds - time_since_last.total_seconds()
                return False, f"Rate limit: wait {wait_time:.1f}s before next call"

        return True, "Call approved"

    def record_call(
        self,
        framework: str,
        test_name: str,
        estimated_cost: float = 0.01,
        tokens_used: Optional[int] = None,
        success: bool = True,
    ) -> None:
        """
        Record an API call for cost tracking.

        Args:
            framework: Name of the framework being tested
            test_name: Name of the specific test
            estimated_cost: Actual or estimated cost of the call
            tokens_used: Number of tokens used (if available)
            success: Whether the call was successful
        """
        record = APICallRecord(
            timestamp=datetime.now(),
            framework=framework,
            test_name=test_name,
            estimated_cost=estimated_cost,
            tokens_used=tokens_used,
            success=success,
        )

        self.call_records.append(record)
        self.last_call_time = datetime.now()

    def wait_for_rate_limit(self) -> None:
        """Wait if needed to respect rate limiting."""
        if self.last_call_time:
            time_since_last = datetime.now() - self.last_call_time
            wait_needed = self.rate_limit_seconds - time_since_last.total_seconds()
            if wait_needed > 0:
                print(f"⏱️  Rate limiting: waiting {wait_needed:.1f}s...")
                time.sleep(wait_needed)

    def get_cost_summary(self) -> Dict:
        """Get summary of API usage and costs."""
        total_calls = len(self.call_records)
        successful_calls = len([r for r in self.call_records if r.success])
        total_cost = sum(r.estimated_cost for r in self.call_records)

        framework_stats = {}
        for record in self.call_records:
            if record.framework not in framework_stats:
                framework_stats[record.framework] = {
                    "calls": 0,
                    "cost": 0.0,
                    "success_rate": 0.0,
                }
            framework_stats[record.framework]["calls"] += 1
            framework_stats[record.framework]["cost"] += record.estimated_cost

        # Calculate success rates
        for framework in framework_stats:
            framework_records = [
                r for r in self.call_records if r.framework == framework
            ]
            successful = len([r for r in framework_records if r.success])
            framework_stats[framework]["success_rate"] = successful / len(
                framework_records
            )

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "total_cost": total_cost,
            "remaining_budget": max(0, self.max_estimated_cost - total_cost),
            "framework_stats": framework_stats,
            "limits": {
                "max_calls_per_framework": self.max_calls_per_framework,
                "max_total_calls": self.max_total_calls,
                "max_cost": self.max_estimated_cost,
            },
        }

    def print_cost_summary(self) -> None:
        """Print a formatted cost summary."""
        summary = self.get_cost_summary()

        print("\n" + "=" * 50)
        print("💰 API USAGE COST SUMMARY")
        print("=" * 50)
        print(
            f"📞 Total calls: {summary['total_calls']}/{summary['limits']['max_total_calls']}"
        )
        print(f"✅ Successful: {summary['successful_calls']}")
        print(f"💵 Total cost: ${summary['total_cost']:.3f}")
        print(f"💰 Remaining budget: ${summary['remaining_budget']:.3f}")

        if summary["framework_stats"]:
            print("\n📊 Framework Breakdown:")
            for framework, stats in summary["framework_stats"].items():
                success_pct = stats["success_rate"] * 100
                calls_limit = summary["limits"]["max_calls_per_framework"]
                print(
                    f"  {framework:15} | {stats['calls']:2d}/{calls_limit} calls | "
                    f"${stats['cost']:.3f} | {success_pct:3.0f}% success"
                )

        print("=" * 50)


def estimate_openai_cost(
    model: str = "gpt-3.5-turbo", input_tokens: int = 100, output_tokens: int = 50
) -> float:
    """
    Estimate OpenAI API cost based on model and token usage.

    Args:
        model: OpenAI model name
        input_tokens: Estimated input tokens
        output_tokens: Estimated output tokens

    Returns:
        Estimated cost in USD
    """
    # Pricing as of 2024 (rates may change)
    pricing = {
        "gpt-3.5-turbo": {"input": 0.0015 / 1000, "output": 0.002 / 1000},
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "text-embedding-ada-002": {"input": 0.0001 / 1000, "output": 0.0},
    }

    if model not in pricing:
        # Default to gpt-3.5-turbo pricing
        model = "gpt-3.5-turbo"

    input_cost = input_tokens * pricing[model]["input"]
    output_cost = output_tokens * pricing[model]["output"]

    return input_cost + output_cost


# Global cost controller instance
_global_controller: Optional[CostController] = None


def get_cost_controller() -> CostController:
    """Get the global cost controller instance."""
    global _global_controller
    if _global_controller is None:
        _global_controller = CostController()
    return _global_controller


def reset_cost_controller() -> None:
    """Reset the global cost controller."""
    global _global_controller
    _global_controller = CostController()


if __name__ == "__main__":
    # Test the cost controller
    controller = CostController(max_calls_per_framework=2, max_total_calls=5)

    # Test some calls
    frameworks = ["langchain", "crewai", "autogen"]

    for i in range(8):  # Try to exceed limits
        framework = frameworks[i % len(frameworks)]
        test_name = f"test_{i}"

        can_proceed, reason = controller.can_make_call(framework, test_name)
        print(f"Call {i+1} ({framework}): {can_proceed} - {reason}")

        if can_proceed:
            controller.record_call(framework, test_name, estimated_cost=0.01)
            controller.wait_for_rate_limit()

    controller.print_cost_summary()
