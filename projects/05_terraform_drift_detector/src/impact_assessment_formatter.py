"""
Formats LLM-generated policy violation impact assessments for better user understanding.

Provides structured formatting for console output, Markdown reports, and structured exports.
"""

from typing import List, Dict, Any
from dataclasses import asdict
from common.utils import get_logger

logger = get_logger(__name__)


class ImpactAssessmentFormatter:
    """Formats LLM-generated impact assessments for various output targets."""
    
    def format_violations(self, violations: List[Any]) -> str:
        """
        Format violations with enhanced impact communication for console output.
        
        Args:
            violations: List of PolicyViolation dataclass instances or dicts
        
        Returns:
            Formatted string suitable for console/Markdown display
        """
        if not violations:
            return "✅ No policy violations detected.\n"
        
        formatted_output = [f"\n⚠️  Policy Violations Summary ({len(violations)} found):\n"]
        formatted_output.append("=" * 80)
        
        # Group by severity for better visibility
        by_severity = self._group_by_severity(violations)
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        for severity in severity_order:
            if severity in by_severity:
                violations_at_level = by_severity[severity]
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}[severity]
                formatted_output.append(f"\n{emoji} {severity} ({len(violations_at_level)})")
                formatted_output.append("-" * 40)
                
                for i, violation in enumerate(violations_at_level, 1):
                    formatted_output.append(self._format_single_violation(violation, i, severity))
        
        formatted_output.append("\n" + "=" * 80)
        return "\n".join(formatted_output)
    
    def format_violations_markdown(self, violations: List[Any]) -> str:
        """
        Format violations for Markdown report export.
        
        Args:
            violations: List of PolicyViolation objects
        
        Returns:
            Markdown-formatted report
        """
        if not violations:
            return "## Policy Compliance\n✅ All resources are compliant.\n"
        
        markdown_output = [
            f"## Policy Violations ({len(violations)} issues)\n",
            self._markdown_table(violations)
        ]
        
        return "\n".join(markdown_output)
    
    def format_violations_json(self, violations: List[Any]) -> Dict[str, Any]:
        """
        Format violations as structured JSON (for APIs/exports).
        
        Args:
            violations: List of PolicyViolation objects
        
        Returns:
            Dictionary suitable for JSON serialization
        """
        # Convert dataclass instances to dicts
        violations_list = []
        for v in violations:
            if hasattr(v, '__dataclass_fields__'):
                violations_list.append(asdict(v))
            else:
                violations_list.append(v)
        
        return {
            "total_violations": len(violations_list),
            "violations": violations_list,
            "severity_breakdown": self._severity_breakdown(violations_list)
        }
    
    def _group_by_severity(self, violations: List[Any]) -> Dict[str, List[Any]]:
        """Group violations by severity level."""
        grouped = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        
        for v in violations:
            severity = getattr(v, 'severity', v.get('severity') if isinstance(v, dict) else None)
            if severity in grouped:
                grouped[severity].append(v)
        
        return {k: v for k, v in grouped.items() if v}  # Remove empty groups
    
    def _format_single_violation(self, violation: Any, index: int, severity: str) -> str:
        """Format a single violation for display."""
        # Handle both dataclass and dict inputs
        if hasattr(violation, '__dict__'):
            v_dict = violation.__dict__
        else:
            v_dict = violation
        
        policy = v_dict.get('policy', 'Unknown')
        section = v_dict.get('section', 'Unknown')
        impact = v_dict.get('impact', 'No details provided')
        frameworks = v_dict.get('compliance_frameworks', [])
        remediation = v_dict.get('remediation')
        confidence = v_dict.get('confidence', 0.0)
        
        output = [
            f"\n  #{index} {policy} → {section}",
            f"     Impact: {impact}",
        ]
        
        if frameworks:
            output.append(f"     Compliance: {', '.join(frameworks)}")
        
        if remediation:
            output.append(f"     Fix: {remediation}")
        
        output.append(f"     Confidence: {confidence * 100:.0f}%")
        
        return "\n".join(output)
    
    def _markdown_table(self, violations: List[Any]) -> str:
        """Generate Markdown table of violations."""
        lines = [
            "| Policy | Section | Severity | Impact | Frameworks | Confidence |",
            "|--------|---------|----------|--------|------------|------------|"
        ]
        
        for v in violations:
            if hasattr(v, '__dict__'):
                v_dict = v.__dict__
            else:
                v_dict = v
            
            policy = v_dict.get('policy', 'N/A').split('/')[-1]  # Just filename
            section = v_dict.get('section', 'N/A')
            severity = v_dict.get('severity', 'N/A')
            impact = v_dict.get('impact', 'N/A')[:50] + "..."  # Truncate
            frameworks = ", ".join(v_dict.get('compliance_frameworks', []))[:20]
            confidence = f"{v_dict.get('confidence', 0.0) * 100:.0f}%"
            
            lines.append(
                f"| {policy} | {section} | {severity} | {impact} | {frameworks} | {confidence} |"
            )
        
        return "\n".join(lines)
    
    def _severity_breakdown(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count violations by severity."""
        breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for v in violations:
            severity = v.get('severity', 'LOW')
            if severity in breakdown:
                breakdown[severity] += 1
        
        return breakdown
