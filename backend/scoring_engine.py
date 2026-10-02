import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path
from backend.config import settings

# NAICS code descriptions reference
NAICS_DESCRIPTIONS = {
    "541511": "Custom Computer Programming Services",
    "541512": "Computer Systems Design Services",
    "541513": "Computer Facilities Management Services",
    "541519": "Other Computer Related Services",
    "518210": "Computing Infrastructure, Data Processing, Web Hosting",
    "541715": "R&D in the Physical, Engineering, and Life Sciences",
    "541690": "Other Scientific and Technical Consulting Services",
    "541330": "Engineering Services",
    "541990": "All Other Professional, Scientific, and Technical Services",
    "511210": "Software Publishers",
    "519130": "Internet Publishing and Broadcasting and Web Search Portals"
}

class ScoringEngine:
    def __init__(self, skills_file_path: Path = None):
        self.skills_file_path = skills_file_path or settings.SKILLS_FILE_PATH
        self.config = self.load_skills_config()

    def load_skills_config(self) -> Dict[str, Any]:
        if not self.skills_file_path.exists():
            raise FileNotFoundError(f"Skills configuration file not found at {self.skills_file_path}")
        with open(self.skills_file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def reload(self):
        self.config = self.load_skills_config()

    def calculate_scorecard(self, solicitation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the full scorecard for a solicitation including executable work likelihood,
        summary of work, category match breakdown, and feasibility analysis.
        """
        title = (solicitation.get("title") or "").strip()
        description = (solicitation.get("description") or "").strip()
        naics = str(solicitation.get("naics_code") or "").strip()
        psc = str(solicitation.get("psc_code") or "").strip().upper()
        
        full_text = f"{title}\n{description}".lower()
        title_lower = title.lower()

        categories = self.config.get("categories", [])
        scoring_params = self.config.get("scoring_parameters", {})
        
        category_scores: Dict[str, float] = {}
        all_matched_keywords: List[str] = []
        matched_naics_flag = False

        # Evaluate each category in the skills file
        weighted_sum = 0.0
        total_category_weight = 0.0

        for cat in categories:
            cat_id = cat.get("id")
            cat_name = cat.get("name")
            cat_weight = float(cat.get("weight", 0.33))
            total_category_weight += cat_weight

            keywords = [k.lower() for k in cat.get("keywords", [])]
            cat_naics = [str(n).strip() for n in cat.get("naics", [])]
            cat_psc = [str(p).strip().upper() for p in cat.get("psc", [])]

            # 1. Match Keywords
            matched_in_cat = []
            for kw in keywords:
                # Word boundary match for short keywords (e.g. api, sql, llm, git), substring for longer phrases
                if len(kw) <= 4:
                    pattern = rf"\b{re.escape(kw)}\b"
                    if re.search(pattern, full_text):
                        matched_in_cat.append(kw)
                else:
                    if kw in full_text:
                        matched_in_cat.append(kw)

            all_matched_keywords.extend(matched_in_cat)

            # Keyword match base score (diminishing returns curve)
            # 1 match -> 40, 2 matches -> 65, 3 matches -> 85, 4+ matches -> 100
            k_count = len(matched_in_cat)
            if k_count == 0:
                keyword_score = 0.0
            elif k_count == 1:
                keyword_score = 45.0
            elif k_count == 2:
                keyword_score = 70.0
            elif k_count == 3:
                keyword_score = 88.0
            else:
                keyword_score = min(100.0, 88.0 + (k_count - 3) * 4.0)

            # Title keyword bonus
            title_boost = 0.0
            for kw in matched_in_cat:
                if kw in title_lower:
                    title_boost = 15.0
                    break

            # NAICS match
            naics_match = naics in cat_naics or any(naics.startswith(cn[:4]) for cn in cat_naics if len(cn) >= 4)
            if naics_match:
                matched_naics_flag = True
                naics_boost = 25.0
            else:
                naics_boost = 0.0

            # PSC match
            psc_boost = 15.0 if psc in cat_psc else 0.0

            # Combined category raw score
            cat_score = min(100.0, keyword_score * 0.60 + title_boost + naics_boost + psc_boost)
            category_scores[cat_id] = round(cat_score, 1)

            weighted_sum += cat_score * cat_weight

        base_score = weighted_sum / (total_category_weight or 1.0)

        # 2. Check for Disqualifiers / Non-target work (e.g. janitorial, construction)
        disqualifiers = scoring_params.get("disqualifying_keywords", [])
        disqualifiers_found = []
        for dkw in disqualifiers:
            if re.search(rf"\b{re.escape(dkw.lower())}\b", full_text):
                disqualifiers_found.append(dkw)

        disqualifier_penalty = 0.0
        if disqualifiers_found:
            # If title explicitly has a disqualifier, high penalty
            title_disqualifiers = [d for d in disqualifiers_found if d in title_lower]
            if title_disqualifiers:
                disqualifier_penalty = float(scoring_params.get("disqualifier_penalty", 35)) * 1.5
            else:
                disqualifier_penalty = float(scoring_params.get("disqualifier_penalty", 35))

        # 3. Check for Deliverable Clarity & Execution Markers
        deliverable_markers = scoring_params.get("deliverable_markers", [])
        found_markers = []
        for dm in deliverable_markers:
            if dm in full_text:
                found_markers.append(dm)

        clarity_boost = min(15.0, len(found_markers) * 3.5)

        # 4. Final Likelihood of Executable Work Score
        final_score = base_score + clarity_boost - disqualifier_penalty
        final_score = max(0.0, min(100.0, final_score))
        final_score = round(final_score, 1)

        # 5. Determine Tier
        thresholds = scoring_params.get("thresholds", {"high_match": 70, "moderate_match": 40})
        if final_score >= thresholds.get("high_match", 70):
            tier = "HIGH"
        elif final_score >= thresholds.get("moderate_match", 40):
            tier = "MODERATE"
        else:
            tier = "LOW"

        # Unique matched keywords
        unique_keywords = sorted(list(set(all_matched_keywords)))

        # 6. Extract Work Deliverables
        deliverables = self._extract_deliverables(description, found_markers)

        # 7. Generate Executive Summary of Work
        summary = self._generate_work_summary(title, description, unique_keywords, deliverables, final_score)

        # 8. Feasibility Analysis Object
        top_cat_id = max(category_scores.items(), key=lambda x: x[1])[0] if category_scores else "none"
        top_cat_name = next((c["name"] for c in categories if c["id"] == top_cat_id), "General")

        feasibility_analysis = {
            "executable_confidence": "High" if tier == "HIGH" else ("Moderate" if tier == "MODERATE" else "Low"),
            "scope_clarity": "Strong" if len(found_markers) >= 3 else ("Moderate" if len(found_markers) >= 1 else "Preliminary"),
            "primary_domain": top_cat_name,
            "deliverable_markers_found": found_markers,
            "disqualifiers_detected": disqualifiers_found,
            "naics_description": NAICS_DESCRIPTIONS.get(naics, "Standard Government Contracting Code"),
            "naics_matched": matched_naics_flag,
            "confidence_factors": {
                "keyword_match_count": len(unique_keywords),
                "scope_markers_count": len(found_markers),
                "penalty_applied": disqualifier_penalty
            }
        }

        return {
            "notice_id": solicitation.get("notice_id"),
            "overall_score": final_score,
            "tier": tier,
            "category_scores": category_scores,
            "matched_keywords": unique_keywords,
            "matched_naics": matched_naics_flag,
            "summary": summary,
            "deliverables": deliverables,
            "feasibility_analysis": feasibility_analysis
        }

    def _extract_deliverables(self, description: str, found_markers: List[str]) -> List[str]:
        """
        Extracts concrete deliverables and tasks from solicitation text.
        """
        deliverables = []
        if not description:
            return ["Review detailed solicitation documents and statement of work on SAM.gov."]

        # Look for bullet points or numbered lists in text
        lines = description.split("\n")
        for line in lines:
            line_strip = line.strip()
            # Check for bullet format (e.g. "-", "*", "1.", "a.")
            if re.match(r"^(\d+[\.\)]|[\-\*\•])\s+", line_strip):
                clean_item = re.sub(r"^(\d+[\.\)]|[\-\*\•])\s+", "", line_strip).strip()
                if len(clean_item) > 15 and len(clean_item) < 220:
                    deliverables.append(clean_item)
                    if len(deliverables) >= 5:
                        break

        # If no bullet points found, extract sentences with deliverable/scope action verbs
        if not deliverables:
            sentences = re.split(r"(?<=[.!?])\s+", description)
            action_verbs = ["develop", "design", "implement", "deploy", "build", "maintain", "provide", "analyze", "migrate", "deliver", "integrate", "support"]
            for s in sentences:
                s_lower = s.lower().strip()
                if any(v in s_lower for v in action_verbs) and len(s) > 25 and len(s) < 200:
                    clean_s = s.strip()
                    # Skip common disclaimer sentences
                    if not any(skip in s_lower for skip in ["this is a notice", "questions regarding", "point of contact", "sam.gov"]):
                        deliverables.append(clean_s)
                        if len(deliverables) >= 4:
                            break

        if not deliverables:
            deliverables = [
                "Full technical execution as outlined in the Statement of Work (SOW).",
                "Technical documentation, architecture blueprints, and source code deliverables.",
                "Periodic status reporting and sprint milestone acceptance reviews."
            ]

        return deliverables

    def _generate_work_summary(self, title: str, description: str, keywords: List[str], deliverables: List[str], score: float) -> str:
        """
        Synthesizes a clean, high-impact summary of the work to be performed.
        """
        if not description or len(description.strip()) < 30:
            if keywords:
                return f"{title}. Work involves {', '.join(keywords[:4])} capabilities required by the contracting agency."
            return f"Solicitation for: {title}. Refer to the official SAM.gov solicitation package for complete scope details."

        # Find the most informative lead sentence
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", description) if len(s.strip()) > 20]
        lead_sentence = ""
        for s in sentences:
            s_clean = s.strip()
            s_lower = s_clean.lower()
            # Look for purpose statements
            if any(p in s_lower for p in ["the contractor shall", "the purpose of this", "seeking qualified", "scope of work includes", "services to provide", "requirement for", "contractor will"]):
                lead_sentence = s_clean
                break
        
        if not lead_sentence and sentences:
            lead_sentence = sentences[0]

        # Clean boilerplate phrases
        lead_sentence = re.sub(r"^(this is a (combined synopsis/solicitation|solicitation|sources sought)[\.\,\s]+)", "", lead_sentence, flags=re.I).strip()
        lead_sentence = lead_sentence[0].upper() + lead_sentence[1:] if lead_sentence else ""

        # Compose summary paragraph
        summary_parts = []
        if lead_sentence:
            summary_parts.append(lead_sentence)
            
        if keywords:
            key_skills = ", ".join(keywords[:5])
            summary_parts.append(f"Key required capabilities include {key_skills}.")
            
        if deliverables and len(deliverables) > 0:
            first_deliv = deliverables[0]
            if not first_deliv.endswith("."):
                first_deliv += "."
            summary_parts.append(f"Primary deliverable focus: {first_deliv}")

        full_summary = " ".join(summary_parts)
        if len(full_summary) > 550:
            full_summary = full_summary[:547] + "..."

        return full_summary

scoring_engine = ScoringEngine()
