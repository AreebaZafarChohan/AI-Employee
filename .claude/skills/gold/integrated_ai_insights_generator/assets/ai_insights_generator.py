#!/usr/bin/env python3
"""
Integrated AI Insights Generator

A Python script that implements an AI-powered insights generator to analyze 
project data, logs, or task metrics and generate actionable insights.
"""

import asyncio
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_insights_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    async def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the source."""
        pass


class JiraDataSource(DataSource):
    """Jira data source implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config['url']
        self.api_token = os.getenv('JIRA_API_TOKEN', config.get('api_token', ''))
        self.username = os.getenv('JIRA_USERNAME', config.get('username', ''))
        self.projects = config['projects']
        self.fields = config['fields']
        self.query_filters = config.get('query_filters', {})
        self.rate_limit = config.get('rate_limit', {}).get('requests_per_minute', 60)
        self.base_url = f"{self.url}/rest/api/3"
    
    async def fetch_data(self) -> pd.DataFrame:
        if not self.enabled:
            logger.info("Jira data source is disabled")
            return pd.DataFrame()
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self._encode_credentials()}'
        }
        
        # Build JQL query
        jql_parts = [f"project in ({','.join(self.projects)})"]
        
        if 'date_range' in self.query_filters:
            if self.query_filters['date_range'] == 'last_90_days':
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                jql_parts.append(f"created >= '{start_date}'")
        
        if 'issue_types' in self.query_filters:
            issue_types = ','.join([f'"{t}"' for t in self.query_filters['issue_types']])
            jql_parts.append(f"issuetype in ({issue_types})")
        
        jql_query = ' AND '.join(jql_parts)
        
        # Prepare request
        params = {
            'jql': jql_query,
            'maxResults': 100,  # Adjust as needed
            'fields': ','.join(self.fields)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert to DataFrame
                        issues = data.get('issues', [])
                        df_data = []
                        
                        for issue in issues:
                            row = {'key': issue['key']}
                            for field in self.fields:
                                row[field] = issue['fields'].get(field, None)
                            df_data.append(row)
                        
                        df = pd.DataFrame(df_data)
                        logger.info(f"Fetched {len(df)} issues from Jira")
                        return df
                    else:
                        logger.error(f"Jira API error: {response.status}")
                        return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching from Jira: {str(e)}")
            return pd.DataFrame()
    
    def _encode_credentials(self):
        """Encode credentials for Basic Auth."""
        import base64
        credentials = f"{self.username}:{self.api_token}"
        return base64.b64encode(credentials.encode()).decode()


class FileDataSource(DataSource):
    """File-based data source implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.path = config['path']
        self.format = config.get('format', 'json')
        self.pattern = config.get('pattern')
        self.encoding = config.get('encoding', 'utf-8')
        self.refresh_interval = config.get('refresh_interval_seconds', 30)
        self.fields = config.get('fields', [])
    
    async def fetch_data(self) -> pd.DataFrame:
        if not self.enabled:
            logger.info("File data source is disabled")
            return pd.DataFrame()
        
        try:
            if self.format == 'json':
                with open(self.path, 'r', encoding=self.encoding) as f:
                    # Read all lines and parse as JSON
                    lines = f.readlines()
                    data = []
                    for line in lines:
                        try:
                            parsed = json.loads(line.strip())
                            data.append(parsed)
                        except json.JSONDecodeError:
                            continue  # Skip invalid lines
                    
                    df = pd.DataFrame(data)
                    logger.info(f"Fetched {len(df)} records from file {self.path}")
                    return df
            elif self.format == 'text' and self.pattern:
                with open(self.path, 'r', encoding=self.encoding) as f:
                    content = f.read()
                    
                # Use regex to extract structured data
                matches = re.findall(self.pattern, content)
                df = pd.DataFrame(matches, columns=self.fields)
                logger.info(f"Fetched {len(df)} records from file {self.path}")
                return df
            else:
                logger.error(f"Unsupported format: {self.format}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error reading file {self.path}: {str(e)}")
            return pd.DataFrame()


class DatabaseDataSource(DataSource):
    """Database data source implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection_string = os.getenv('DATABASE_CONNECTION_STRING', 
                                          config.get('connection_string', ''))
        self.table = config['table']
        self.query = config.get('query', f'SELECT * FROM {self.table}')
        self.fields = config.get('fields', [])
        self.refresh_interval = config.get('refresh_interval_seconds', 60)
    
    async def fetch_data(self) -> pd.DataFrame:
        if not self.enabled:
            logger.info("Database data source is disabled")
            return pd.DataFrame()
        
        try:
            # For this example, we'll simulate database access
            # In a real implementation, you would use a database connector
            logger.warning("Database connection not implemented in this example. Returning mock data.")
            
            # Create mock data for demonstration
            n_records = 100
            df = pd.DataFrame({
                'task_id': [f'task_{i}' for i in range(n_records)],
                'start_time': pd.date_range(start='2023-01-01', periods=n_records, freq='H'),
                'end_time': pd.date_range(start='2023-01-01 01:00:00', periods=n_records, freq='H'),
                'duration': np.random.randint(10, 120, n_records),
                'status': np.random.choice(['completed', 'failed', 'in_progress'], n_records),
                'assigned_to': np.random.choice(['Alice', 'Bob', 'Charlie', 'Diana'], n_records),
                'priority': np.random.choice(['low', 'medium', 'high'], n_records),
                'project_id': np.random.choice(['PROJ1', 'PROJ2', 'PROJ3'], n_records)
            })
            
            logger.info(f"Fetched {len(df)} records from database table {self.table}")
            return df
        except Exception as e:
            logger.error(f"Error querying database: {str(e)}")
            return pd.DataFrame()


class AIModelInterface:
    """Interface to AI models for generating insights."""
    
    def __init__(self, config: Dict[str, Any]):
        self.provider = config['provider']
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.api_key = os.getenv('OPENAI_API_KEY', config.get('api_key', ''))
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 1000)
        self.timeout = config.get('request_timeout', 30)
        self.base_url = 'https://api.openai.com/v1/chat/completions'
    
    async def generate_insights(self, prompt: str) -> str:
        """Generate insights using AI model."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"AI model API error: {response.status}")
                        return f"Error: AI model API returned status {response.status}"
        except asyncio.TimeoutError:
            logger.error("AI model request timed out")
            return "Error: Request to AI model timed out"
        except Exception as e:
            logger.error(f"Error calling AI model: {str(e)}")
            return f"Error: Failed to call AI model - {str(e)}"


class AnalysisTechnique(ABC):
    """Abstract base class for analysis techniques."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform analysis on the data."""
        pass


class TrendAnalysis(AnalysisTechnique):
    """Trend analysis technique implementation."""
    
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in the data."""
        if data.empty:
            return {"error": "No data to analyze"}
        
        results = {}
        
        # Look for numeric columns to analyze trends
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            if len(data[col].dropna()) < 2:
                continue  # Need at least 2 points for trend analysis
            
            # Prepare data for regression
            clean_data = data.dropna(subset=[col])
            if 'index' not in data.columns:
                clean_data = clean_data.reset_index()
            
            # Use index as time proxy for trend analysis
            X = clean_data.index.values.reshape(-1, 1)
            y = clean_data[col].values
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Calculate trend metrics
            slope = model.coef_[0]
            intercept = model.intercept_
            r_squared = model.score(X, y)
            
            # Predict next values
            next_x = np.array([[len(clean_data)]])
            next_y = model.predict(next_x)[0]
            
            results[col] = {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "next_predicted_value": float(next_y)
            }
        
        return {
            "analysis_type": "trend_analysis",
            "results": results,
            "summary": f"Analyzed trends in {len(results)} numeric columns"
        }


class AnomalyDetection(AnalysisTechnique):
    """Anomaly detection technique implementation."""
    
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in the data."""
        if data.empty:
            return {"error": "No data to analyze"}
        
        # Select numeric columns for anomaly detection
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            return {"error": "No numeric data for anomaly detection"}
        
        # Normalize the data
        normalized_data = (numeric_data - numeric_data.mean()) / numeric_data.std()
        
        # Apply Isolation Forest
        contamination = self.config.get('contamination', 0.1)
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        anomalies = iso_forest.fit_predict(normalized_data)
        
        # Get anomaly indices
        anomaly_indices = np.where(anomalies == -1)[0]
        
        # Prepare results
        results = {
            "anomaly_count": len(anomaly_indices),
            "anomaly_percentage": len(anomaly_indices) / len(data) * 100,
            "anomaly_indices": anomaly_indices.tolist(),
            "anomaly_details": []
        }
        
        # Add details for each anomaly
        for idx in anomaly_indices[:10]:  # Limit to first 10 for brevity
            if idx < len(data):
                anomaly_row = data.iloc[idx].to_dict()
                results["anomaly_details"].append({
                    "index": int(idx),
                    "row_data": {k: str(v) for k, v in anomaly_row.items()}
                })
        
        return {
            "analysis_type": "anomaly_detection",
            "results": results,
            "summary": f"Detected {len(anomaly_indices)} anomalies in the dataset"
        }


class InsightsGenerator:
    """Main class for generating AI-powered insights."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.data_sources = {}
        self.ai_interface = None
        self.analysis_techniques = {}
        self.session = None
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load insights generator configuration from the configuration file."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize data sources
        for source_name, source_config in config.get('data_sources', {}).items():
            if source_config.get('enabled', True):
                source_type = source_config['type']
                
                if source_type == 'jira':
                    self.data_sources[source_name] = JiraDataSource(source_config)
                elif source_type == 'file':
                    self.data_sources[source_name] = FileDataSource(source_config)
                elif source_type == 'database':
                    self.data_sources[source_name] = DatabaseDataSource(source_config)
                else:
                    logger.warning(f"Unknown data source type: {source_type}")
        
        # Initialize AI interface
        ai_config = config.get('ai_configuration', {})
        self.ai_interface = AIModelInterface(ai_config)
        
        # Initialize analysis techniques
        analysis_config = config.get('analysis_settings', {})
        
        if analysis_config.get('trend_analysis', {}).get('enabled', True):
            self.analysis_techniques['trend'] = TrendAnalysis(
                analysis_config['trend_analysis']
            )
        
        if analysis_config.get('anomaly_detection', {}).get('enabled', True):
            self.analysis_techniques['anomaly'] = AnomalyDetection(
                analysis_config['anomaly_detection']
            )
        
        logger.info(f"Loaded configuration with {len(self.data_sources)} data sources")
    
    async def initialize(self):
        """Initialize the insights generator."""
        self.session = aiohttp.ClientSession()
        logger.info("AI Insights Generator initialized")
    
    async def close(self):
        """Close the insights generator and clean up resources."""
        if self.session:
            await self.session.close()
        logger.info("AI Insights Generator closed")
    
    async def fetch_all_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch data from all enabled data sources."""
        data = {}
        
        for name, source in self.data_sources.items():
            logger.info(f"Fetching data from {name}...")
            df = await source.fetch_data()
            if not df.empty:
                data[name] = df
            else:
                logger.warning(f"No data fetched from {name}")
        
        return data
    
    async def perform_analysis(self, data: Dict[str, pd.DataFrame], analysis_types: List[str]) -> Dict[str, Any]:
        """Perform specified analyses on the data."""
        results = {}
        
        for analysis_type in analysis_types:
            if analysis_type in self.analysis_techniques:
                logger.info(f"Performing {analysis_type} analysis...")
                
                # Combine all data sources for analysis
                combined_data = pd.concat(data.values(), ignore_index=True, sort=False)
                
                technique = self.analysis_techniques[analysis_type]
                result = technique.analyze(combined_data)
                results[analysis_type] = result
            else:
                logger.warning(f"Unknown analysis type: {analysis_type}")
        
        return results
    
    async def generate_ai_insights(self, analysis_results: Dict[str, Any], data_summaries: Dict[str, str]) -> str:
        """Generate AI-powered insights based on analysis results."""
        # Create a prompt for the AI model
        prompt_parts = [
            "You are an expert data analyst. Analyze the following data analysis results and provide actionable insights.",
            "\nDATA SUMMARIES:",
        ]
        
        for source_name, summary in data_summaries.items():
            prompt_parts.append(f"\n{source_name.upper()} DATA:\n{summary}")
        
        prompt_parts.append("\nANALYSIS RESULTS:")
        for analysis_type, result in analysis_results.items():
            prompt_parts.append(f"\n{analysis_type.upper()} ANALYSIS:\n{json.dumps(result, indent=2)}")
        
        prompt_parts.extend([
            "\nPlease provide:",
            "1. Key findings from the analysis",
            "2. Potential issues or concerns identified",
            "3. Actionable recommendations based on the data",
            "4. Areas that require further investigation",
            "5. Any trends or patterns that stand out"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        logger.info("Generating AI insights...")
        ai_response = await self.ai_interface.generate_insights(prompt)
        
        return ai_response
    
    async def generate_insights(
        self, 
        data_sources: List[str] = None, 
        analysis_types: List[str] = ["trend", "anomaly"],
        include_ai_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Generate insights from specified data sources using specified analysis types.
        
        Args:
            data_sources: List of data source names to use (if None, use all enabled sources)
            analysis_types: List of analysis types to perform
            include_ai_insights: Whether to generate AI-powered insights
        
        Returns:
            Dictionary containing analysis results and AI insights
        """
        # Fetch data from specified sources
        all_data = await self.fetch_all_data()
        
        if data_sources:
            data = {k: v for k, v in all_data.items() if k in data_sources}
        else:
            data = all_data
        
        if not data:
            logger.error("No data sources available for analysis")
            return {"error": "No data sources available for analysis"}
        
        # Create data summaries
        data_summaries = {}
        for name, df in data.items():
            if not df.empty:
                summary = (
                    f"Dataset: {name}\n"
                    f"Rows: {len(df)}\n"
                    f"Columns: {list(df.columns)}\n"
                    f"Date Range: {df.iloc[0].name if hasattr(df.iloc[0], 'name') else 'N/A'} "
                    f"to {df.iloc[-1].name if hasattr(df.iloc[-1], 'name') else 'N/A'}\n"
                    f"Numeric Columns: {list(df.select_dtypes(include=[np.number]).columns)}"
                )
                data_summaries[name] = summary
        
        # Perform analysis
        analysis_results = await self.perform_analysis(data, analysis_types)
        
        # Generate AI insights if requested
        ai_insights = ""
        if include_ai_insights:
            ai_insights = await self.generate_ai_insights(analysis_results, data_summaries)
        
        # Compile final results
        results = {
            "timestamp": datetime.now().isoformat(),
            "data_sources_used": list(data.keys()),
            "analysis_types_performed": analysis_types,
            "analysis_results": analysis_results,
            "ai_insights": ai_insights,
            "summary": {
                "total_data_sources": len(data),
                "total_rows_processed": sum(len(df) for df in data.values()),
                "analyses_performed": len(analysis_results)
            }
        }
        
        logger.info(f"Generated insights from {len(data)} data sources")
        return results


class InsightsServer:
    """HTTP server for receiving insights generation requests."""
    
    def __init__(self, generator: InsightsGenerator, port: int = 8083):
        self.generator = generator
        self.port = port
    
    async def handle_generate_insights(self, request):
        """Handle incoming insights generation requests."""
        try:
            data = await request.json()
            
            data_sources = data.get('data_sources')
            analysis_types = data.get('analysis_types', ['trend', 'anomaly'])
            include_ai_insights = data.get('include_ai_insights', True)
            
            results = await self.generator.generate_insights(
                data_sources=data_sources,
                analysis_types=analysis_types,
                include_ai_insights=include_ai_insights
            )
            
            return aiohttp.web.json_response({
                'success': True,
                'results': results
            })
        except Exception as e:
            logger.error(f"Error handling insights request: {str(e)}")
            return aiohttp.web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def start_server(self):
        """Start the HTTP server."""
        app = aiohttp.web.Application()
        app.router.add_post('/generate-insights', self.handle_generate_insights)
        
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        
        site = aiohttp.web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"Insights server started on port {self.port}")
        
        # Keep the server running
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()


async def main():
    """Main entry point for the AI insights generator."""
    # Default paths
    config_path = os.getenv("INSIGHTS_GENERATOR_CONFIG_PATH", "./assets/data_sources_config.json")
    
    # Create insights generator
    generator = InsightsGenerator(config_path)
    await generator.initialize()
    
    # Create and start server
    server = InsightsServer(generator)
    
    try:
        # Run the server in the background
        server_task = asyncio.create_task(server.start_server())
        
        # Generate some sample insights
        logger.info("Generating sample insights...")
        results = await generator.generate_insights(
            data_sources=None,  # Use all available sources
            analysis_types=['trend', 'anomaly'],
            include_ai_insights=True
        )
        
        logger.info("Sample insights generated successfully")
        logger.info(f"Summary: {results.get('summary', {})}")
        
        # Show first few hundred characters of AI insights
        ai_insights = results.get('ai_insights', '')
        if ai_insights:
            logger.info(f"AI Insights Preview: {ai_insights[:500]}...")
        
        # Keep running for demonstration
        await asyncio.sleep(30)  # Run for 30 seconds for demo
        
        # Cancel the server task
        server_task.cancel()
        await server_task
        
    except KeyboardInterrupt:
        logger.info("Shutting down AI insights generator...")
        await generator.close()
    except Exception as e:
        logger.error(f"Error in AI insights generator: {str(e)}")
        await generator.close()


if __name__ == "__main__":
    asyncio.run(main())