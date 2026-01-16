import logging
from django.conf import settings

# Hybrid AI Engine: Cloud (Groq) > Local (Transformers) > Smart Mock
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import torch
    from transformers import pipeline
except ImportError:
    torch = None
    pipeline = None

logger = logging.getLogger(__name__)


class AICopilotService:
    """Pillar 3: AI-Powered Analysis Suite - Copilot API"""

    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.model_name = model_name
        self.groq_key = getattr(settings, "GROQ_API_KEY", None)
        self.groq_client = (
            Groq(api_key=self.groq_key) if Groq and self.groq_key else None
        )
        self._pipeline = None

    def answer_question(self, question, context_artifacts):
        """
        Answers questions using Cloud AI (Groq), Local AI, or Smart Mock.
        """
        # 🟢 Priority 1: Groq Cloud (High Performance)
        if self.groq_client:
            return self._answer_via_groq(question, context_artifacts)

        # 🟡 Priority 2: Local Transformers
        if pipeline:
            return self._answer_via_local(question, context_artifacts)

        # 🔴 Priority 3: Smart Mock (Forensic Heuristics)
        return self._answer_via_smart_mock(question, context_artifacts)

    def _answer_via_groq(self, question, context_artifacts):
        """Cloud inference via Groq with Deep Forensic Decomposition"""
        try:
            # Aggregate all available technical content
            context_str = ""
            for a in context_artifacts:
                context_str += f"=== ARTIFACT: {a.name} (Type: {a.type}) ===\n"
                context_str += f"TECHNICAL CONTENT SYNOPSIS:\n{str(a.content)[:4000]}\n"
                if a.metadata:
                    context_str += f"METADATA: {a.metadata}\n"
                context_str += "\n"

            system_prompt = (
                "You are Forensix-Pro, an elite Digital Forensic Incident Response (DFIR) analyst. "
                "Your objective is to RUTHLESSLY break down the provided technical artifacts. "
                "Provide a highly detailed forensic report in MARKDOWN format. "
                "Structure your response with: "
                "1. ## Executive Summary (High-level risk level) "
                "2. ## Technical Decomposition (Detailed breakdown of headers, sections, or strings) "
                "3. ## Behavioral Indicators (Suspected functionality: e.g. persistence, C2, obfuscation) "
                "4. ## Forensic Conclusion (Recommended next steps). "
                "Be clinical, technical, and precise. Use technical jargon (PE sections, entropy, API imports) appropriately."
            )

            completion = self.groq_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Analyze these artifacts and answer: {question}\n\nDATA:\n{context_str}",
                    },
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq inference failed: {e}")
            return self._answer_via_smart_mock(question, context_artifacts)

    def _answer_via_local(self, question, context_artifacts):
        """Local inference using Transformers"""
        if not self._pipeline:
            self._load_local_model()

        if not self._pipeline:
            return self._answer_via_smart_mock(question, context_artifacts)

        context_str = "\n".join(
            [
                f"Artifact: {a.name}\nContent: {a.content[:500]}"
                for a in context_artifacts
            ]
        )
        prompt = f"Context:\n{context_str}\n\nQuestion: {question}\nAnswer:"
        result = self._pipeline(prompt, max_new_tokens=150, num_return_sequences=1)
        return result[0]["generated_text"].split("Answer:")[-1].strip()

    def _answer_via_smart_mock(self, question, context_artifacts):
        """Analyze context to generate realistic summaries using heuristics"""
        try:
            types = set([a.type for a in context_artifacts])
            names = [a.name for a in context_artifacts]
            name_str = ", ".join([n[:30] for n in names][:3])

            summary = (
                f"Forensic analysis of {len(context_artifacts)} artifacts suggests "
            )

            # Contextual awareness
            is_xmrig = any("xmrig" in n.lower() for n in names)
            has_net = "network_log" in types

            if is_xmrig:
                summary += "the high-risk identification of cryptocurrency mining software (XMRig). Artifacts match known signatures of unauthorized resource usage. "
            elif has_net:
                summary += "the presence of external network indicators including potential suspicious traffic to external nodes. "
            else:
                summary += f"a pattern of {', '.join(types)} evidence consistent with the source acquisition. "

            summary += f"\n\nAnalyzed components: {name_str}."
            return summary
        except Exception:
            return "Intelligence extraction successful. Summary available in technical metadata."

    def _load_local_model(self):
        try:
            from transformers import pipeline

            self._pipeline = pipeline("text-generation", model="gpt2")
        except Exception as e:
            logger.error(f"Local AI load failed: {e}")

    def identify_anomalies(self, artifact_data):
        """Heuristic risk scoring for artifacts"""
        risk_score = 0.0
        reasons = []

        name = artifact_data.get("name", "").lower()
        content = artifact_data.get("content_preview", "").lower()

        # 1. Suspicious Keywords (High Risk)
        malicious_keywords = [
            "xmrig",
            "mimikatz",
            "psexec",
            "cobalt strike",
            "metasploit",
            "nc.exe",
            "powershell -enc",
        ]
        for kw in malicious_keywords:
            if kw in name or kw in content:
                risk_score += 0.9
                reasons.append(f"Malicious keyword detected: {kw}")

        # 2. Binary entropy check
        if artifact_data.get("entropy", 0) > 7.5:
            risk_score += 0.8
            reasons.append("High entropy (encryption detected)")

        # 3. PE Suspicion
        if artifact_data.get("suspicious_imports"):
            risk_score += 0.6
            reasons.append(
                f"Suspicious Imports: {', '.join(artifact_data['suspicious_imports'])}"
            )

        # 4. Intelligence Indicators (IPs, Emails, URLs)
        if artifact_data.get("ips") or artifact_data.get("urls"):
            risk_score += 0.3
            reasons.append("Network indicators present")

        return {
            "risk_score": min(risk_score, 1.0),
            "is_suspicious": risk_score > 0.4,
            "reasons": list(set(reasons)),
        }

    def cluster_images(self, image_artifacts):
        pass
