import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

# Sample realistic solicitations spanning Technology, Data Analysis, Software Dev, and Non-tech controls
MOCK_SOLICITATIONS: List[Dict[str, Any]] = [
    {
        "notice_id": "SAM-2026-DISA-00192",
        "sol_number": "HC108426R0012",
        "title": "DISA Enterprise Cloud Application Development & DevSecOps Services",
        "agency": "Department of Defense",
        "office": "Defense Information Systems Agency (DISA)",
        "posted_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=28)).strftime("%Y-%m-%d"),
        "naics_code": "541511",
        "psc_code": "DA01",
        "set_aside": "Total Small Business Set-Aside",
        "type": "Solicitation",
        "description": """The Defense Information Systems Agency (DISA) requires comprehensive software development, DevSecOps pipeline engineering, and cloud application modernization services. 
The contractor shall design, develop, test, and deploy resilient web applications and microservices in secure cloud environments (AWS GovCloud and Azure Government).
Core Deliverables:
- Build containerized backend microservices using Python FastAPI and Node.js with secure RESTful APIs.
- Deliver responsive, modern web application frontends using TypeScript and modern JavaScript frameworks.
- Automate CI/CD pipelines incorporating automated SAST/DAST testing, container scanning, and zero trust security validation.
- Provide sprint milestone reports, source code documentation, and automated testing suites under agile scrum ceremonies.
All personnel must adhere to DoD Zero Trust Architecture and FedRAMP High baseline requirements.""",
        "place_of_performance": "Fort Meade, MD / Remote Friendly",
        "ui_link": "https://sam.gov/opp/SAM-2026-DISA-00192/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-VA-00843",
        "sol_number": "36C10B26Q0145",
        "title": "Veterans Health Administration Clinical Data Analytics & AI Dashboard Platform",
        "agency": "Department of Veterans Affairs",
        "office": "Office of Information and Technology (OIT)",
        "posted_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=21)).strftime("%Y-%m-%d"),
        "naics_code": "541512",
        "psc_code": "DA10",
        "set_aside": "Service-Disabled Veteran-Owned Small Business (SDVOSB)",
        "type": "Combined Synopsis/Solicitation",
        "description": """The Department of Veterans Affairs (VA) requires advanced data analysis, machine learning modeling, and interactive business intelligence dashboard development.
The purpose of this requirement is to synthesize large-scale patient outcomes and healthcare operations datasets to provide predictive analytics for clinical staffing and patient care quality.
Scope of Work:
- Architect automated ETL data pipelines extracting data from enterprise SQL data warehouses and electronic health records.
- Develop interactive, role-based business intelligence dashboards utilizing Power BI and modern web visualization libraries.
- Build predictive analytics and natural language processing (NLP) models to uncover trends in unstructured clinical notes.
- Establish robust data governance, automated data quality validations, and compliance with HIPAA and VA security protocols.
Deliverables include functional dashboards, data pipeline code repositories, statistical analysis reports, and sprint acceptance reviews.""",
        "place_of_performance": "Austin, TX / Remote",
        "ui_link": "https://sam.gov/opp/SAM-2026-VA-00843/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-HHS-00331",
        "sol_number": "75N95026R00054",
        "title": "HHS/NIH Genomic Data Science & Cloud Analytics Modernization",
        "agency": "Department of Health and Human Services",
        "office": "National Institutes of Health (NIH)",
        "posted_date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=35)).strftime("%Y-%m-%d"),
        "naics_code": "518210",
        "psc_code": "DB02",
        "set_aside": "Unrestricted",
        "type": "Solicitation",
        "description": """The National Institutes of Health is seeking qualified technical teams to develop scalable cloud infrastructure and data analytics tools for biomedical research datasets.
Key contractor responsibilities:
- Implement distributed data engineering pipelines using cloud-native compute (AWS, Google Cloud).
- Provide machine learning and statistical analysis capabilities for researchers querying multi-terabyte datasets.
- Develop standardized RESTful API endpoints for researchers to query dataset metadata and download scientific subsets.
- Deliver comprehensive technical documentation, architecture diagrams, and user guides.
Vendors must demonstrate strong experience with big data processing, Python data science toolkits, and secure cloud storage.""",
        "place_of_performance": "Bethesda, MD / Hybrid",
        "ui_link": "https://sam.gov/opp/SAM-2026-HHS-00331/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-NASA-00912",
        "sol_number": "80GSFC26R0032",
        "title": "NASA Goddard Space Flight Center Telemetry Data Visualization & Custom Web Platform",
        "agency": "National Aeronautics and Space Administration",
        "office": "Goddard Space Flight Center",
        "posted_date": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=19)).strftime("%Y-%m-%d"),
        "naics_code": "541511",
        "psc_code": "DA01",
        "set_aside": "Total Small Business Set-Aside",
        "type": "Solicitation",
        "description": """NASA GSFC requires specialized software development services for spacecraft mission operations and flight data visualization.
The contractor shall design, implement, and maintain a full stack web application to stream and visualize real-time mission telemetry.
Required Deliverables:
- Interactive frontend visualization application built with TypeScript, React, and WebSockets for low-latency streaming.
- High-throughput Python microservices backend connecting to distributed time-series databases.
- Integration of automated unit testing, end-to-end integration tests, and containerized Docker deployments.
- Performance work statement milestone demonstrations every two weeks according to agile development practices.""",
        "place_of_performance": "Greenbelt, MD / Remote Eligible",
        "ui_link": "https://sam.gov/opp/SAM-2026-NASA-00912/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-DHS-00449",
        "sol_number": "70B04C26Q0000078",
        "title": "CISA Cyber Threat Intelligence Automated Reporting & API Integration",
        "agency": "Department of Homeland Security",
        "office": "Cybersecurity and Infrastructure Security Agency (CISA)",
        "posted_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "naics_code": "541519",
        "psc_code": "DJ01",
        "set_aside": "8(a) Sole Source / Set-Aside",
        "type": "Solicitation",
        "description": """CISA requires professional software engineering and data analytics support to enhance the automated cyber threat intelligence sharing pipeline.
The objective is to ingest real-time threat indicators (STIX/TAXII), perform algorithmic deduplication and risk scoring, and distribute automated alerts to critical infrastructure stakeholders.
Scope of Work:
- Construct robust Python ETL pipelines integrating external cybersecurity threat feeds via REST APIs.
- Build automated reporting dashboards and KPI tracking for vulnerability response times.
- Ensure strict adherence to NIST 800-53 security controls, Zero Trust standards, and role-based access management.
Deliverables: Python codebase, Swagger API documentation, integration test plans, and bi-weekly sprint deliverables.""",
        "place_of_performance": "Arlington, VA / Remote",
        "ui_link": "https://sam.gov/opp/SAM-2026-DHS-00449/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-GSA-00718",
        "sol_number": "47QTCB26R0089",
        "title": "GSA Federal Acquisition Service Data Warehouse Modernization & Analytics Support",
        "agency": "General Services Administration",
        "office": "Federal Acquisition Service (FAS)",
        "posted_date": (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=40)).strftime("%Y-%m-%d"),
        "naics_code": "541512",
        "psc_code": "DA10",
        "set_aside": "HUBZone",
        "type": "Solicitation",
        "description": """GSA FAS has an ongoing requirement to modernize its legacy transaction reporting systems into an enterprise cloud data warehouse.
The contractor will provide senior data engineers and analysts to:
- Migrate relational data pipelines to modern cloud analytics warehouses (BigQuery/Snowflake).
- Develop automated SQL data modeling transformations and data quality monitoring suites.
- Create automated executive dashboards summarizing federal procurement trends and spending metrics.
- Provide user training and technical transition documentation.""",
        "place_of_performance": "Washington, DC / Remote",
        "ui_link": "https://sam.gov/opp/SAM-2026-GSA-00718/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-DOD-ROOF-991",
        "sol_number": "W9127826B0033",
        "title": "US Army Corps of Engineers Barracks Roof Replacement and Asphalt Paving",
        "agency": "Department of the Army",
        "office": "US Army Corps of Engineers (USACE)",
        "posted_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "naics_code": "238160",
        "psc_code": "Z1AA",
        "set_aside": "Total Small Business Set-Aside",
        "type": "Solicitation",
        "description": """The contractor shall provide all labor, heavy equipment, and materials for roofing replacement and asphalt paving at Fort Liberty, NC. Work includes tear-off of 45,000 sq ft of membrane roofing, structural repairs, flashing replacement, concrete curb repair, and parking lot asphalt resurfacing.""",
        "place_of_performance": "Fort Liberty, NC",
        "ui_link": "https://sam.gov/opp/SAM-2026-DOD-ROOF-991/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    },
    {
        "notice_id": "SAM-2026-VA-JANITORIAL-772",
        "sol_number": "36C24526Q0211",
        "title": "VA Medical Center Comprehensive Custodial & Janitorial Floor Care Services",
        "agency": "Department of Veterans Affairs",
        "office": "Network Contracting Office (NCO 5)",
        "posted_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "response_date": (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d"),
        "naics_code": "561720",
        "psc_code": "S201",
        "set_aside": "Service-Disabled Veteran-Owned Small Business (SDVOSB)",
        "type": "Solicitation",
        "description": """The VA Medical Center requires complete janitorial and custodial cleaning services. Contractor will supply cleaning supplies, trash removal, terminal floor waxing, hospital disinfection, and restroom sanitation seven days a week across medical facilities.""",
        "place_of_performance": "Baltimore, MD",
        "ui_link": "https://sam.gov/opp/SAM-2026-VA-JANITORIAL-772/view",
        "raw_data": {"source": "MOCK_SIMULATED"}
    }
]

class SamGovClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SAM_API_KEY
        self.base_url = settings.SAM_API_BASE_URL

    async def fetch_opportunities(
        self,
        days_back: int = 1,
        limit: int = 50,
        ptype: str = "o,k"
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Fetches opportunities from SAM.gov API or falls back to realistic simulation if no API key is provided.
        Returns (list_of_solicitations, status_message)
        """
        if not self.api_key or self.api_key.strip() == "":
            logger.info("No SAM.gov API key configured. Using rich simulated solicitation feed.")
            return MOCK_SOLICITATIONS, "SIMULATION_MODE: Realistic mock solicitations loaded (Provide SAM_API_KEY for live data)"

        # Calculate date range in MM/dd/yyyy format required by SAM.gov API
        now = datetime.utcnow()
        posted_from = (now - timedelta(days=days_back)).strftime("%m/%d/%Y")
        posted_to = now.strftime("%m/%d/%Y")

        params = {
            "api_key": self.api_key.strip(),
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "limit": str(limit),
            "ptype": ptype,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    raw_items = data.get("opportunitiesData", [])
                    logger.info(f"Successfully retrieved {len(raw_items)} opportunities from SAM.gov API.")
                    parsed = [self._normalize_sam_opportunity(item) for item in raw_items]
                    return parsed, f"LIVE_SUCCESS: Retrieved {len(parsed)} solicitations from SAM.gov API"
                
                elif response.status_code in (401, 403):
                    msg = f"SAM.gov API Authentication Failed ({response.status_code}). Verify your SAM_API_KEY. Falling back to test data."
                    logger.warning(msg)
                    return MOCK_SOLICITATIONS, msg
                
                else:
                    msg = f"SAM.gov API Error ({response.status_code}): {response.text[:200]}. Falling back to test data."
                    logger.error(msg)
                    return MOCK_SOLICITATIONS, msg

        except Exception as e:
            msg = f"Network or connection error communicating with SAM.gov: {str(e)}. Falling back to test data."
            logger.error(msg)
            return MOCK_SOLICITATIONS, msg

    def _normalize_sam_opportunity(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps SAM.gov API payload to standardized internal schema
        """
        notice_id = item.get("noticeId") or item.get("_id") or str(item.get("solicitationNumber", "UNKNOWN"))
        ui_link = item.get("uiLink") or f"https://sam.gov/opp/{notice_id}/view"

        # Determine description
        desc = item.get("description", "")
        if isinstance(desc, list) and len(desc) > 0:
            desc = desc[0]

        # Extract place of performance
        pop_obj = item.get("placeOfPerformance") or {}
        pop_str = ""
        if isinstance(pop_obj, dict):
            city = pop_obj.get("city", {}).get("name", "") if isinstance(pop_obj.get("city"), dict) else pop_obj.get("city", "")
            state = pop_obj.get("state", {}).get("code", "") if isinstance(pop_obj.get("state"), dict) else pop_obj.get("state", "")
            pop_str = f"{city}, {state}".strip(", ")

        return {
            "notice_id": notice_id,
            "sol_number": item.get("solicitationNumber") or item.get("solNumber") or "N/A",
            "title": item.get("title") or "Untitled Solicitation",
            "agency": item.get("department") or item.get("agency") or "Federal Government",
            "office": item.get("subTier") or item.get("office") or "",
            "posted_date": item.get("postedDate") or datetime.utcnow().strftime("%Y-%m-%d"),
            "response_date": item.get("responseDeadLine") or item.get("responseDate") or "",
            "naics_code": str(item.get("naicsCode") or item.get("naics") or ""),
            "psc_code": str(item.get("classificationCode") or item.get("psc") or ""),
            "set_aside": item.get("typeOfSetAsideDescription") or item.get("typeOfSetAside") or "Unrestricted",
            "type": item.get("type") or "Solicitation",
            "description": desc,
            "place_of_performance": pop_str,
            "ui_link": ui_link,
            "raw_data": item
        }

sam_client = SamGovClient()
