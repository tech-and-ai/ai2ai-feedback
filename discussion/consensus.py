"""
Consensus Building

This module provides functionality for building consensus in discussions.
"""

import logging
from typing import Dict, List, Optional, Any

from models.message import Message
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class ConsensusBuilder:
    """Consensus builder class."""
    
    def __init__(self, model_router: ModelRouter, prompt_manager: PromptManager):
        """
        Initialize the consensus builder.
        
        Args:
            model_router: Model router
            prompt_manager: Prompt manager
        """
        self.model_router = model_router
        self.prompt_manager = prompt_manager
        logger.info("Initialized consensus builder")
    
    async def analyze_discussion(self, 
                               messages: List[Message], 
                               agent_model: str,
                               system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a discussion to identify consensus and disagreements.
        
        Args:
            messages: List of messages in the discussion
            agent_model: Model to use for analysis
            system_prompt: Optional system prompt
            
        Returns:
            Analysis results
        """
        # Format messages for analysis
        formatted_messages = self._format_messages(messages)
        
        # Create analysis prompt
        prompt = f"""
        Analyze the following discussion and identify areas of consensus and disagreement:

        {formatted_messages}

        Please provide:
        1. A summary of the discussion
        2. Key points of consensus
        3. Key points of disagreement
        4. Suggested next steps to reach consensus
        """
        
        # Use model to analyze discussion
        from models.agent import Agent
        
        agent = Agent(
            id="consensus_analyzer",
            name="Consensus Analyzer",
            description="Agent for analyzing discussions and identifying consensus",
            model=agent_model,
            status="available",
            last_active="",
            capabilities={},
            configuration={}
        )
        
        analysis = await self.model_router.route_request(
            prompt=prompt,
            agent=agent,
            system_prompt=system_prompt or "You are an expert at analyzing discussions and identifying areas of consensus and disagreement.",
            max_tokens=2000
        )
        
        # Parse analysis
        return self._parse_analysis(analysis)
    
    async def suggest_resolution(self, 
                               messages: List[Message], 
                               analysis: Dict[str, Any],
                               agent_model: str,
                               system_prompt: Optional[str] = None) -> str:
        """
        Suggest a resolution based on discussion analysis.
        
        Args:
            messages: List of messages in the discussion
            analysis: Analysis results
            agent_model: Model to use for suggestion
            system_prompt: Optional system prompt
            
        Returns:
            Suggested resolution
        """
        # Format messages for resolution
        formatted_messages = self._format_messages(messages)
        
        # Create resolution prompt
        prompt = f"""
        Based on the following discussion and analysis, suggest a resolution that addresses all key points and concerns:

        Discussion:
        {formatted_messages}

        Analysis:
        - Summary: {analysis.get('summary', '')}
        - Consensus: {analysis.get('consensus', [])}
        - Disagreements: {analysis.get('disagreements', [])}

        Please provide a comprehensive resolution that:
        1. Addresses all key points of disagreement
        2. Builds on areas of consensus
        3. Is specific and actionable
        4. Balances the interests of all participants
        """
        
        # Use model to suggest resolution
        from models.agent import Agent
        
        agent = Agent(
            id="resolution_suggester",
            name="Resolution Suggester",
            description="Agent for suggesting resolutions to discussions",
            model=agent_model,
            status="available",
            last_active="",
            capabilities={},
            configuration={}
        )
        
        resolution = await self.model_router.route_request(
            prompt=prompt,
            agent=agent,
            system_prompt=system_prompt or "You are an expert at finding resolutions to complex discussions that address all key points and concerns.",
            max_tokens=2000
        )
        
        return resolution
    
    def _format_messages(self, messages: List[Message]) -> str:
        """
        Format messages for analysis.
        
        Args:
            messages: List of messages
            
        Returns:
            Formatted messages
        """
        formatted = []
        
        for message in messages:
            formatted.append(f"Agent {message.agent_id}: {message.content}")
        
        return "\n\n".join(formatted)
    
    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        """
        Parse analysis results.
        
        Args:
            analysis: Analysis text
            
        Returns:
            Parsed analysis
        """
        # Simple parsing - in a real implementation, use a more robust approach
        lines = analysis.split('\n')
        
        result = {
            'summary': '',
            'consensus': [],
            'disagreements': [],
            'next_steps': []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            if line.lower().startswith('summary'):
                current_section = 'summary'
            elif line.lower().startswith('consensus') or line.lower().startswith('key points of consensus'):
                current_section = 'consensus'
            elif line.lower().startswith('disagreement') or line.lower().startswith('key points of disagreement'):
                current_section = 'disagreements'
            elif line.lower().startswith('next steps') or line.lower().startswith('suggested next steps'):
                current_section = 'next_steps'
            elif current_section:
                if current_section == 'summary':
                    result['summary'] += line + ' '
                elif current_section in ('consensus', 'disagreements', 'next_steps'):
                    if line.startswith('-') or line.startswith('*') or line.startswith('1.') or line.startswith('2.'):
                        result[current_section].append(line.lstrip('- *123456789.').strip())
        
        return result
