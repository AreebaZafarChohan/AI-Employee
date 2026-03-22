import os
import logging
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Import sub-modules
from revenue_analysis import RevenueAnalysis
from productivity_analysis import ProductivityAnalysis
from marketing_analysis import MarketingAnalysis

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class BusinessAnalyticsOrchestrator:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.briefings_dir = self.vault_path / "Briefings" / "Weekly"
        self.briefings_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not found. AI insights will be skipped.")

    def run_all_analysis(self):
        """Runs all sub-analysis modules and returns the paths to the generated reports."""
        logger.info("Starting comprehensive business analysis...")
        
        rev_analyser = RevenueAnalysis(self.vault_path)
        rev_report = rev_analyser.generate_report()
        
        prod_analyser = ProductivityAnalysis(self.vault_path)
        prod_report = prod_analyser.generate_report()
        
        mark_analyser = MarketingAnalysis(self.vault_path)
        mark_report = mark_analyser.generate_report()
        
        return [rev_report, prod_report, mark_report]

    def generate_ceo_briefing(self, report_paths):
        """Uses Gemini to synthesize all reports into a Weekly CEO Briefing."""
        if not self.model:
            logger.error("Cannot generate CEO briefing without Gemini API.")
            return

        report_contents = []
        for path in report_paths:
            with open(path, 'r', encoding='utf-8') as f:
                report_contents.append(f"--- REPORT: {path.name} ---\n{f.read()}\n")

        combined_context = "\n".join(report_contents)
        
        prompt = f"""
        You are a high-level Business Intelligence Consultant for a Personal AI Employee.
        Analyze the following weekly reports and generate a "Weekly CEO Briefing".
        
        Include the following sections:
        1. Executive Overview
        2. Key Financial Highlights
        3. Productivity Assessment
        4. Marketing Performance
        5. STRATEGIC SUGGESTIONS (List at least 3 high-impact actions like 'Reduce spending', 'Increase frequency', 'Follow up')
        6. Growth Opportunities
        
        Reports Context:
        {combined_context}
        """
        
        logger.info("Generating Weekly CEO Briefing via Gemini...")
        response = self.model.generate_content(prompt)
        briefing_text = response.text
        
        report_date = datetime.now().strftime("%Y-%m-%d")
        briefing_path = self.briefings_dir / f"Weekly_CEO_Briefing_{report_date}.md"
        
        content = f"""---
type: ceo_briefing
date: {report_date}
---

{briefing_text}

---
*Synthesized by Gemini AI Business Intelligence Module*
"""
        with open(briefing_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Weekly CEO Briefing finalized: {briefing_path}")
        return briefing_path

if __name__ == "__main__":
    orchestrator = BusinessAnalyticsOrchestrator("AI-Employee-Vault")
    reports = orchestrator.run_all_analysis()
    orchestrator.generate_ceo_briefing(reports)
