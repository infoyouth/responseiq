#!/usr/bin/env python3
"""
P2 Proof-Oriented Remediation Demo

Demonstrates the complete P2 workflow:
Scan → Reproduce → Verify → Remediate → Verify

This script shows how ResponseIQ now moves beyond "trust me" fixes
to proof-backed recommendations using local LLM analysis.
"""

import asyncio
import json
from pathlib import Path

from responseiq.services.reproduction_service import ReproductionService
from responseiq.services.remediation_service import RemediationService
from responseiq.schemas.proof import ValidationEvidence


async def demo_p2_workflow():
    """
    Demonstrate complete P2 proof-oriented remediation workflow.
    """
    print("🚀 ResponseIQ P2: Proof-Oriented Remediation Demo")
    print("=" * 60)
    
    # Step 1: Create high-impact incident that triggers P2
    high_impact_incident = {
        "id": "demo-network-issue-001",
        "severity": "high", 
        "description": "ConnectionError: HTTPSConnectionPool(host='api.payments.com', port=443): Max retries exceeded with url: /v1/charge (Caused by NewConnectionError)",
        "source": "production_monitoring",
        "log_content": """
        2026-02-13T09:30:15Z ERROR [payment-service] Connection failed to payments API
        requests.exceptions.ConnectionError: HTTPSConnectionPool(host='api.payments.com', port=443): Max retries exceeded
        Traceback (most recent call last):
          File "payment_processor.py", line 87, in process_charge
            response = requests.post("https://api.payments.com/v1/charge", json=payload)
          File "requests/adapters.py", line 516, in send
        """
    }
    
    # Step 2: Initialize services 
    reproduction_service = ReproductionService()
    remediation_service = RemediationService(environment="production")
    
    print(f"🔍 Step 1: Analyzing incident [{high_impact_incident['id']}]")
    print(f"   Severity: {high_impact_incident['severity']}")
    print(f"   Description: {high_impact_incident['description'][:80]}...")
    
    # Step 3: Generate remediation recommendation (includes P2 proof generation)
    print("\n📋 Step 2: Generating remediation recommendation...")
    recommendation = await remediation_service.remediate_incident(high_impact_incident)
    
    print(f"   Impact Score: {recommendation.impact_score:.1f}")
    print(f"   Trust Gate Result: {'✅ ALLOWED' if recommendation.allowed else '❌ DENIED'}")
    print(f"   Execution Mode: {recommendation.execution_mode.value if recommendation.execution_mode else 'N/A'}")
    
    # Step 4: Show P2 proof bundle (if generated)
    if recommendation.proof_bundle:
        print(f"\n🧪 Step 3: P2 Proof Bundle Generated (Impact ≥ 40)")
        proof = recommendation.proof_bundle
        print(f"   Reproduction Test: {proof.reproduction_test.test_path}")
        print(f"   Environment Type: {proof.reproduction_test.environment_type}")
        print(f"   Incident Signature: {proof.reproduction_test.incident_signature}")
        print(f"   Reproduction Confidence: {proof.reproduction_confidence:.2f}")
        print(f"   Missing Evidence: {len(proof.missing_evidence)} items")
        
        # Show the first few lines of generated test
        test_file = Path(proof.reproduction_test.test_path)
        if test_file.exists():
            print(f"\n📝 Generated Test Preview:")
            with open(test_file) as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):  # First 10 lines
                    print(f"   {i+1:2d}: {line.rstrip()}")
                if len(lines) > 10:
                    print(f"   ... ({len(lines) - 10} more lines)")
                    
        # Step 5: Execute reproduction test (simulate "Verify Failure")
        print(f"\n🔬 Step 4: Executing reproduction test...")
        updated_proof = await reproduction_service.execute_reproduction_test(proof)
        
        print(f"   Test Status: {updated_proof.reproduction_test.status.value}")
        if updated_proof.pre_fix_evidence:
            print(f"   ✅ Pre-fix failure evidence captured")
        
        # Step 6: Simulate fix application and re-test
        print(f"\n🔧 Step 5: Simulating fix application...")
        print("   (In real workflow: apply remediation_plan changes)")
        
        # Step 7: Validate fix (simulate "Verify Fix")  
        print(f"\n✅ Step 6: Validating fix effectiveness...")
        validated_proof = await reproduction_service.validate_fix_with_reproduction(updated_proof)
        
        if validated_proof.post_fix_evidence and "PASSED" in validated_proof.post_fix_evidence:
            print(f"   ✅ Fix validation: SUCCESS (confidence: {validated_proof.fix_confidence:.2f})")
            print(f"   ✅ Reproduction test now passes")
        else:
            print(f"   ❌ Fix validation: FAILED")
            
        print(f"\n📊 P2 Proof Summary:")
        print(f"   Complete Proof: {'✅ YES' if validated_proof.has_complete_proof else '❌ NO'}")
        print(f"   Blocks Guarded Apply: {'❌ YES' if validated_proof.blocks_guarded_apply else '✅ NO'}")
        
    else:
        print(f"\n⚠️  P2 Proof Generation: SKIPPED (Impact < 40)")
        
    # Step 8: Show final recommendation
    print(f"\n📋 Final Remediation Recommendation:")
    print(f"   Title: {recommendation.title}")
    print(f"   Plan: {recommendation.remediation_plan[:100]}...")
    print(f"   Affected Files: {len(recommendation.affected_files)} files")
    print(f"   Trust Level: {'HIGH' if recommendation.allowed else 'REQUIRES_REVIEW'}")
    
    print(f"\n🎯 P2 Achievement: Moving from 'Trust Me' to 'Proof-Backed' Fixes!")
    print("=" * 60)


async def demo_local_llm_capabilities():
    """
    Quick demo of local LLM capabilities for different incident types.
    """
    print(f"\n🤖 Local Mock LLM Analysis Demo")
    print("=" * 40)
    
    from responseiq.ai.local_llm_service import analyze_with_local_llm
    
    incidents = [
        "ConnectionError: Connection refused to database server",
        "FileNotFoundError: config.json not found in /etc/app/",
        "PermissionError: [Errno 13] Permission denied: '/var/log/app.log'",
        "MemoryError: Unable to allocate 8GB memory for data processing",
        "ModuleNotFoundError: No module named 'missing_dependency'"
    ]
    
    for incident in incidents:
        print(f"\n🔍 Analyzing: {incident}")
        result = await analyze_with_local_llm(incident)
        print(f"   → {result['title']} (confidence: {result['confidence']:.2f})")
        print(f"   → Severity: {result['severity']}")


async def main():
    """Run the complete P2 demonstration."""
    await demo_p2_workflow()
    await demo_local_llm_capabilities()


if __name__ == "__main__":
    asyncio.run(main())