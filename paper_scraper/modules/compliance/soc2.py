"""SOC2 Type II control definitions and status tracking."""

from datetime import UTC, datetime

# SOC2 Trust Services Criteria (TSC) Controls
# Based on 2017 Trust Services Criteria for Security, Availability, Processing Integrity,
# Confidentiality, and Privacy

SOC2_CONTROLS = {
    "CC1": {
        "name": "Control Environment",
        "description": "Management and governance commitment to integrity and ethics",
        "controls": [
            {
                "id": "CC1.1",
                "description": "The entity demonstrates a commitment to integrity and ethical values",
                "status": "implemented",
                "notes": "Code of conduct established and communicated to all employees",
                "evidence_url": None,
            },
            {
                "id": "CC1.2",
                "description": "The board of directors demonstrates independence from management",
                "status": "pending",
                "notes": "Governance structure being formalized",
                "evidence_url": None,
            },
            {
                "id": "CC1.3",
                "description": "Management establishes structures, reporting lines, and authorities",
                "status": "implemented",
                "notes": "Organizational chart and role definitions documented",
                "evidence_url": None,
            },
            {
                "id": "CC1.4",
                "description": "The entity demonstrates commitment to attract and retain competent individuals",
                "status": "implemented",
                "notes": "HR policies and procedures established",
                "evidence_url": None,
            },
            {
                "id": "CC1.5",
                "description": "The entity holds individuals accountable for their internal control responsibilities",
                "status": "implemented",
                "notes": "Performance reviews include security responsibilities",
                "evidence_url": None,
            },
        ],
    },
    "CC2": {
        "name": "Communication and Information",
        "description": "Information and communication systems support control objectives",
        "controls": [
            {
                "id": "CC2.1",
                "description": "The entity obtains or generates relevant information",
                "status": "implemented",
                "notes": "Audit logging captures all security-relevant events",
                "evidence_url": None,
            },
            {
                "id": "CC2.2",
                "description": "The entity internally communicates information to support functioning of controls",
                "status": "implemented",
                "notes": "Security policies published in internal knowledge base",
                "evidence_url": None,
            },
            {
                "id": "CC2.3",
                "description": "The entity communicates with external parties regarding matters affecting controls",
                "status": "in_progress",
                "notes": "Privacy policy and terms of service published",
                "evidence_url": None,
            },
        ],
    },
    "CC3": {
        "name": "Risk Assessment",
        "description": "Risk identification and assessment processes",
        "controls": [
            {
                "id": "CC3.1",
                "description": "The entity specifies objectives with clarity to enable risk identification",
                "status": "implemented",
                "notes": "Security objectives documented in security policy",
                "evidence_url": None,
            },
            {
                "id": "CC3.2",
                "description": "The entity identifies risks to achievement of objectives",
                "status": "in_progress",
                "notes": "Risk assessment framework being implemented",
                "evidence_url": None,
            },
            {
                "id": "CC3.3",
                "description": "The entity considers the potential for fraud in assessing risks",
                "status": "pending",
                "notes": "Fraud risk assessment pending",
                "evidence_url": None,
            },
            {
                "id": "CC3.4",
                "description": "The entity identifies and assesses changes that could impact controls",
                "status": "implemented",
                "notes": "Change management process includes security review",
                "evidence_url": None,
            },
        ],
    },
    "CC4": {
        "name": "Monitoring Activities",
        "description": "Selection, development, and performance of control monitoring",
        "controls": [
            {
                "id": "CC4.1",
                "description": "The entity selects and develops ongoing and separate evaluations",
                "status": "implemented",
                "notes": "Continuous monitoring via Langfuse and Sentry",
                "evidence_url": None,
            },
            {
                "id": "CC4.2",
                "description": "The entity evaluates and communicates control deficiencies",
                "status": "implemented",
                "notes": "Incident response process documents and tracks deficiencies",
                "evidence_url": None,
            },
        ],
    },
    "CC5": {
        "name": "Control Activities",
        "description": "Selection and development of control activities",
        "controls": [
            {
                "id": "CC5.1",
                "description": "The entity selects and develops control activities that mitigate risks",
                "status": "implemented",
                "notes": "Security controls implemented based on risk assessment",
                "evidence_url": None,
            },
            {
                "id": "CC5.2",
                "description": "The entity deploys control activities through policies and procedures",
                "status": "implemented",
                "notes": "Security policies documented and enforced",
                "evidence_url": None,
            },
            {
                "id": "CC5.3",
                "description": "The entity deploys control activities over technology infrastructure",
                "status": "implemented",
                "notes": "Infrastructure as code with security controls",
                "evidence_url": None,
            },
        ],
    },
    "CC6": {
        "name": "Logical and Physical Access Controls",
        "description": "Access control and authentication mechanisms",
        "controls": [
            {
                "id": "CC6.1",
                "description": "The entity implements logical access security software and infrastructure",
                "status": "implemented",
                "notes": "JWT-based authentication with role-based access control",
                "evidence_url": None,
            },
            {
                "id": "CC6.2",
                "description": "Prior to issuing credentials, the entity registers and authorizes new users",
                "status": "implemented",
                "notes": "User registration requires email verification and admin approval",
                "evidence_url": None,
            },
            {
                "id": "CC6.3",
                "description": "The entity authorizes, modifies, or removes access based on roles",
                "status": "implemented",
                "notes": "RBAC system with admin, member, and viewer roles",
                "evidence_url": None,
            },
            {
                "id": "CC6.4",
                "description": "The entity restricts physical access to facilities and assets",
                "status": "not_applicable",
                "notes": "Cloud-hosted infrastructure; physical access managed by cloud provider",
                "evidence_url": None,
            },
            {
                "id": "CC6.5",
                "description": "The entity discontinues access when no longer required",
                "status": "implemented",
                "notes": "User deactivation feature removes all access immediately",
                "evidence_url": None,
            },
            {
                "id": "CC6.6",
                "description": "The entity implements controls to prevent or detect threats",
                "status": "implemented",
                "notes": "Rate limiting, input validation, and security headers implemented",
                "evidence_url": None,
            },
            {
                "id": "CC6.7",
                "description": "The entity restricts transmission and movement of data",
                "status": "implemented",
                "notes": "TLS encryption for all data in transit; tenant isolation enforced",
                "evidence_url": None,
            },
            {
                "id": "CC6.8",
                "description": "The entity implements controls to prevent introduction of unauthorized code",
                "status": "implemented",
                "notes": "CI/CD pipeline includes security scanning; signed commits required",
                "evidence_url": None,
            },
        ],
    },
    "CC7": {
        "name": "System Operations",
        "description": "System monitoring and incident response",
        "controls": [
            {
                "id": "CC7.1",
                "description": "The entity uses detection and monitoring procedures",
                "status": "implemented",
                "notes": "Sentry for error monitoring; Langfuse for LLM observability",
                "evidence_url": None,
            },
            {
                "id": "CC7.2",
                "description": "The entity monitors system components for anomalies",
                "status": "implemented",
                "notes": "Automated alerting on error rates and performance degradation",
                "evidence_url": None,
            },
            {
                "id": "CC7.3",
                "description": "The entity evaluates security events to determine impact",
                "status": "in_progress",
                "notes": "Incident response procedures being documented",
                "evidence_url": None,
            },
            {
                "id": "CC7.4",
                "description": "The entity responds to identified security incidents",
                "status": "implemented",
                "notes": "Incident response team identified; escalation procedures in place",
                "evidence_url": None,
            },
            {
                "id": "CC7.5",
                "description": "The entity identifies and remediates system failures",
                "status": "implemented",
                "notes": "Post-incident review process established",
                "evidence_url": None,
            },
        ],
    },
    "CC8": {
        "name": "Change Management",
        "description": "Change authorization and testing procedures",
        "controls": [
            {
                "id": "CC8.1",
                "description": "The entity authorizes, designs, develops, and implements changes",
                "status": "implemented",
                "notes": "Pull request workflow with required reviews",
                "evidence_url": None,
            },
        ],
    },
    "CC9": {
        "name": "Risk Mitigation",
        "description": "Risk mitigation activities and vendor management",
        "controls": [
            {
                "id": "CC9.1",
                "description": "The entity identifies and mitigates business disruption risks",
                "status": "in_progress",
                "notes": "Business continuity plan in development",
                "evidence_url": None,
            },
            {
                "id": "CC9.2",
                "description": "The entity assesses and manages risks from vendors",
                "status": "in_progress",
                "notes": "Vendor assessment checklist being implemented",
                "evidence_url": None,
            },
        ],
    },
}


def get_soc2_status() -> dict:
    """Get the current SOC2 control status with summary.

    Returns:
        Dict containing control categories and summary statistics.
    """
    categories = []
    total_controls = 0
    status_counts = {
        "implemented": 0,
        "in_progress": 0,
        "pending": 0,
        "not_applicable": 0,
    }

    for code, category in SOC2_CONTROLS.items():
        controls = []
        for control in category["controls"]:
            controls.append({
                "id": control["id"],
                "description": control["description"],
                "status": control["status"],
                "evidence_url": control.get("evidence_url"),
                "notes": control.get("notes"),
                "last_reviewed": None,  # Would be tracked in database in production
            })
            total_controls += 1
            status_counts[control["status"]] += 1

        categories.append({
            "code": code,
            "name": category["name"],
            "controls": controls,
        })

    summary = {
        "total_controls": total_controls,
        "status_counts": status_counts,
        "compliance_percentage": round(
            (status_counts["implemented"] / total_controls) * 100, 1
        ) if total_controls > 0 else 0,
        "last_updated": datetime.now(UTC).isoformat(),
    }

    return {
        "categories": categories,
        "summary": summary,
    }


def get_control_evidence(control_id: str) -> dict | None:
    """Get evidence documentation for a specific control.

    Args:
        control_id: The control ID (e.g., "CC6.1").

    Returns:
        Dict containing evidence items or None if control not found.
    """
    # Parse category from control ID
    category_code = control_id.split(".")[0]

    if category_code not in SOC2_CONTROLS:
        return None

    category = SOC2_CONTROLS[category_code]
    for control in category["controls"]:
        if control["id"] == control_id:
            # In production, this would query a database for evidence documents
            return {
                "control_id": control_id,
                "evidence_items": [
                    {
                        "type": "policy",
                        "name": f"Security Policy - {category['name']}",
                        "url": None,
                        "uploaded_at": None,
                    },
                    {
                        "type": "screenshot",
                        "name": "Implementation Screenshot",
                        "url": None,
                        "uploaded_at": None,
                    },
                ],
            }

    return None
