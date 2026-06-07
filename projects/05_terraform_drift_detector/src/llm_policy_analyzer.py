"""
LLM-based policy violation analyzer using Ollama for enhanced impact assessment.

Replaces heuristic rules with intelligent LLM analysis of drift details against
policy files, providing detailed impact assessment and compliance framework mapping.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys

# Ensure monorepo root is in sys.path for 'common' imports
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from common.llm_factory import get_chat_llm
from common.utils import get_logger

logger = get_logger(__name__)


@dataclass
class PolicyViolation:
    """Enhanced policy violation with impact analysis."""
    policy: str                          # Path to policy file (e.g., "policies/tags.yaml")
    section: str                         # Policy section/key (e.g., "tag_compliance.required_tags")
    severity: str                        # CRITICAL|HIGH|MEDIUM|LOW
    impact: str                          # Detailed explanation of consequences
    compliance_frameworks: List[str]     # Affected frameworks (e.g., ["SOC2", "HIPAA"])
    remediation: Optional[str] = None    # Suggested fix
    confidence: float = 0.85             # LLM confidence in violation detection


class LLMPolicyAnalyzer:
    """Analyzes policy violations using Ollama LLM for enhanced impact understanding."""
    
    def __init__(self, policy_dir: Optional[str] = None, model_override: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            policy_dir: Directory containing policy YAML files (default: policies/ relative to project root)
            model_override: Override default model (for testing/experimentation)
        """
        self.llm = get_chat_llm(model=model_override) if model_override else get_chat_llm()
        
        # Determine policy directory
        if policy_dir is None:
            # Find project root (where policies/ folder exists)
            current = Path(__file__).parent.parent  # src/ -> project root
            policy_dir = str(current / "policies")
        
        self.policy_dir = Path(policy_dir)
        self.policies = self._load_policies()
        
        logger.info(f"LLMPolicyAnalyzer initialized with {len(self.policies)} policy files from {self.policy_dir}")
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load all YAML policies from policy directory."""
        policies = {}
        
        if not self.policy_dir.exists():
            logger.warning(f"Policy directory not found: {self.policy_dir}")
            return policies
        
        for yaml_file in self.policy_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    policies[yaml_file.name] = yaml.safe_load(f)
                logger.debug(f"Loaded policy file: {yaml_file.name}")
            except Exception as e:
                logger.error(f"Failed to load policy {yaml_file.name}: {e}")
        
        return policies
    
    def analyze_violations(self, resource_type: str, drift_type: str, 
                          severity: str, changes: Dict[str, Any]) -> List[PolicyViolation]:
        """
        Analyze drift details using LLM for enhanced policy violation detection.
        
        Args:
            resource_type: AWS resource type (e.g., "aws_instance", "aws_security_group")
            drift_type: Type of drift (e.g., "tags_modified", "attributes_changed")
            severity: Severity level (CRITICAL|HIGH|MEDIUM|LOW)
            changes: Dictionary of changes detected in the resource
        
        Returns:
            List of PolicyViolation objects with detailed impact analysis
        """
        # Create structured prompt with drift context and policies
        prompt_text = self._create_analysis_prompt(resource_type, drift_type, severity, changes)
        
        try:
            # Create prompt and parser
            prompt = PromptTemplate(
                input_variables=["analysis_request"],
                template="{analysis_request}"
            )
            
            parser = JsonOutputParser()
            chain = prompt | self.llm | parser
            
            # Invoke LLM
            result = chain.invoke({"analysis_request": prompt_text})
            
            # Parse and convert to PolicyViolation objects
            violations = self._parse_llm_response(result)
            
            logger.info(f"LLM analysis identified {len(violations)} violations for {resource_type} ({drift_type})")
            return violations
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}. Falling back to heuristic extraction.", exc_info=True)
            return self._fallback_heuristic_extraction(resource_type, drift_type, severity, changes)
    
    def _create_analysis_prompt(self, resource_type: str, drift_type: str, 
                               severity: str, changes: Dict[str, Any]) -> str:
        """
        Create detailed prompt for LLM analysis including policy context.
        
        Args:
            resource_type: AWS resource type
            drift_type: Type of drift detected
            severity: Initial severity assessment
            changes: Dictionary of specific changes
        
        Returns:
            Formatted prompt string for LLM
        """
        policies_context = self._format_policies_for_context()
        
        return f"""You are an expert compliance and infrastructure analyst. Analyze the following AWS resource drift against applicable policies.

RESOURCE DRIFT DETAILS:
- Resource Type: {resource_type}
- Drift Type: {drift_type}
- Initial Severity: {severity}
- Changes Detected: {json.dumps(changes, indent=2)}

APPLICABLE POLICIES:
{policies_context}

ANALYSIS TASK:
Identify ALL relevant policy violations that this drift triggers. For each violation:
1. Reference the exact policy file and section (e.g., "policies/tags.yaml → tag_compliance.required_tags")
2. Assess actual severity (CRITICAL|HIGH|MEDIUM|LOW) considering impact
3. Explain detailed impact on operations, compliance, and business continuity
4. Identify affected compliance frameworks (SOC2, HIPAA, PCI-DSS, ISO27001, INFRASTRUCTURE_AS_CODE, etc.)
5. Suggest specific remediation steps
6. Provide confidence level (0-1) in the violation assessment

Return a JSON object with this structure:
{{
    "violations": [
        {{
            "policy": "policies/filename.yaml",
            "section": "policy.section.path",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "impact": "Detailed explanation of consequences...",
            "compliance_frameworks": ["FRAMEWORK1", "FRAMEWORK2"],
            "remediation": "Specific fix steps...",
            "confidence": 0.85
        }}
    ],
    "summary": "Brief summary of overall compliance implications"
}}

Focus on accuracy over quantity. Only report violations that are clearly supported by the drift details."""
    
    def _format_policies_for_context(self) -> str:
        """Format loaded policies for inclusion in LLM prompt."""
        if not self.policies:
            return "No policies loaded. Using general compliance framework knowledge."
        
        formatted = []
        for filename, content in self.policies.items():
            try:
                formatted.append(f"**File: {filename}**\n{yaml.dump(content, default_flow_style=False)}")
            except Exception as e:
                logger.warning(f"Could not format policy {filename}: {e}")
        
        return "\n".join(formatted)
    
    def _parse_llm_response(self, response: Dict[str, Any]) -> List[PolicyViolation]:
        """
        Parse LLM response into structured PolicyViolation objects.
        
        Args:
            response: Dictionary returned by LLM (should contain 'violations' key)
        
        Returns:
            List of PolicyViolation objects
        """
        violations = []
        
        if not isinstance(response, dict):
            logger.warning(f"Unexpected response type: {type(response)}")
            return violations
        
        violations_data = response.get("violations", [])
        if not isinstance(violations_data, list):
            logger.warning(f"Expected 'violations' to be a list, got {type(violations_data)}")
            return violations
        
        for v in violations_data:
            try:
                # Validate required fields
                required = ["policy", "section", "severity", "impact", "compliance_frameworks"]
                if not all(field in v for field in required):
                    logger.warning(f"Violation missing required fields: {v}")
                    continue
                
                # Ensure severity is valid
                if v["severity"] not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                    logger.warning(f"Invalid severity level: {v['severity']}")
                    v["severity"] = "MEDIUM"
                
                violation = PolicyViolation(
                    policy=str(v["policy"]),
                    section=str(v["section"]),
                    severity=str(v["severity"]),
                    impact=str(v["impact"]),
                    compliance_frameworks=v.get("compliance_frameworks", []),
                    remediation=v.get("remediation"),
                    confidence=float(v.get("confidence", 0.85))
                )
                violations.append(violation)
            except Exception as e:
                logger.warning(f"Failed to parse violation: {e}")
                continue
        
        return violations
    
    def _fallback_heuristic_extraction(self, resource_type: str, drift_type: str, 
                                      severity: str, changes: dict) -> List[PolicyViolation]:
        """
        Fallback heuristic extraction when LLM analysis fails.
        
        Provides sensible defaults based on drift characteristics.
        """
        violations = []
        
        # Tag-related drifts
        if drift_type == "tags_modified" and changes:
            removed_tags = changes.get("removed_tags", [])
            modified_tags = changes.get("modified_tags", {})
            
            if removed_tags or modified_tags:
                violations.append(PolicyViolation(
                    policy="policies/tags.yaml",
                    section="tag_compliance.required_tags",
                    severity=severity or "HIGH",
                    impact=f"Missing or modified required tags on {resource_type}. Affects resource identification, cost tracking, compliance tracking, and operational automation.",
                    compliance_frameworks=["AWS_TAGGING_POLICY", "SOC2", "ISO27001"],
                    remediation=f"Apply required tags to {resource_type} using Terraform or AWS Console",
                    confidence=0.75
                ))
        
        # Attribute/configuration changes
        elif drift_type == "attributes_changed":
            violations.append(PolicyViolation(
                policy="policies/resource_configuration.yaml",
                section="configuration_baseline.immutable_settings",
                severity=severity or "MEDIUM",
                impact=f"Configuration drift detected on {resource_type}. Manual changes outside Terraform may cause infrastructure-as-code violations and future apply failures.",
                compliance_frameworks=["INFRASTRUCTURE_AS_CODE"],
                remediation=f"Reconcile manual changes by either: 1) Apply terraform apply, or 2) Update .tf files to match live state",
                confidence=0.70
            ))
        
        # Resource lifecycle (created/deleted outside Terraform)
        elif drift_type in ["resource_created", "resource_deleted"]:
            violations.append(PolicyViolation(
                policy="policies/resource_lifecycle.yaml",
                section="lifecycle_control.terraform_managed_resources",
                severity=severity or "CRITICAL",
                impact=f"Resource lifecycle violation: {resource_type} managed outside Terraform. Breaks infrastructure-as-code principles and change management controls.",
                compliance_frameworks=["INFRASTRUCTURE_AS_CODE", "CHANGE_MANAGEMENT"],
                remediation=f"Import resource into Terraform state (terraform import) or remove resource and recreate via Terraform",
                confidence=0.90
            ))
        
        logger.info(f"Used heuristic fallback: {len(violations)} violations extracted")
        return violations
