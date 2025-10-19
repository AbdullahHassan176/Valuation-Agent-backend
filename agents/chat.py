"""
Constrained chat agent for valuation runs using LangGraph
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime
import requests
from dataclasses import dataclass
from enum import Enum

# LangGraph imports (simplified implementation)
from typing import TypedDict, Literal


class ChatState(TypedDict):
    """State for the chat agent"""
    messages: List[Dict[str, Any]]
    run_id: Optional[str]
    current_tool: Optional[str]
    tool_result: Optional[Dict[str, Any]]
    response: Optional[str]
    error: Optional[str]


class ToolType(Enum):
    """Available tool types"""
    GET_RUN_STATUS = "get_run_status"
    RUN_SENSITIVITY = "run_sensitivity"
    EXPLAIN_RUN = "explain_run"
    ABSTAIN = "abstain"


@dataclass
class ToolCall:
    """Tool call definition"""
    name: str
    parameters: Dict[str, Any]
    description: str


class ConstrainedChatAgent:
    """Constrained chat agent that can only perform specific actions"""
    
    def __init__(self):
        self.allowed_tools = {
            "get_run_status": {
                "description": "Get the status and details of a valuation run",
                "parameters": ["run_id"]
            },
            "run_sensitivity": {
                "description": "Run sensitivity analysis on a valuation run",
                "parameters": ["run_id", "shock_type", "shock_value"]
            },
            "explain_run": {
                "description": "Get an explanation of a valuation run using RAG",
                "parameters": ["run_id"]
            }
        }
        
        self.abstain_keywords = [
            "price", "calculate", "compute", "value", "barrier", "option", 
            "swaption", "cap", "floor", "exotic", "derivative", "invent",
            "create", "generate", "make up", "fabricate", "estimate"
        ]
    
    def should_abstain(self, message: str) -> bool:
        """Check if the message should trigger abstention"""
        message_lower = message.lower()
        
        # Check for abstain keywords
        for keyword in self.abstain_keywords:
            if keyword in message_lower:
                return True
        
        # Check for specific forbidden patterns
        forbidden_patterns = [
            "price a", "calculate a", "value a", "compute a",
            "invent", "make up", "fabricate", "estimate"
        ]
        
        for pattern in forbidden_patterns:
            if pattern in message_lower:
                return True
        
        return False
    
    def parse_tool_request(self, message: str, run_id: str) -> Optional[ToolCall]:
        """Parse user message and determine appropriate tool call"""
        message_lower = message.lower()
        
        # Check for abstention first
        if self.should_abstain(message):
            return ToolCall(
                name="abstain",
                parameters={"reason": "Request involves pricing/calculation outside allowed scope"},
                description="Abstain from unauthorized request"
            )
        
        # Parse sensitivity requests
        if any(word in message_lower for word in ["sensitivity", "shock", "bump", "parallel", "twist"]):
            shock_type = "parallel"
            shock_value = 1.0  # Default 1bp
            
            if "parallel" in message_lower:
                if "+1bp" in message_lower or "+1 bp" in message_lower:
                    shock_value = 1.0
                elif "-1bp" in message_lower or "-1 bp" in message_lower:
                    shock_value = -1.0
                elif "+10bp" in message_lower or "+10 bp" in message_lower:
                    shock_value = 10.0
                elif "-10bp" in message_lower or "-10 bp" in message_lower:
                    shock_value = -10.0
            
            return ToolCall(
                name="run_sensitivity",
                parameters={
                    "run_id": run_id,
                    "shock_type": shock_type,
                    "shock_value": shock_value
                },
                description=f"Run {shock_type} sensitivity analysis with {shock_value}bp shock"
            )
        
        # Parse explanation requests
        if any(word in message_lower for word in ["explain", "why", "reason", "rationale", "methodology"]):
            return ToolCall(
                name="explain_run",
                parameters={"run_id": run_id},
                description="Get explanation of the valuation run"
            )
        
        # Parse status requests
        if any(word in message_lower for word in ["status", "state", "progress", "result", "details"]):
            return ToolCall(
                name="get_run_status",
                parameters={"run_id": run_id},
                description="Get run status and details"
            )
        
        # Default to abstention if unclear
        return ToolCall(
            name="abstain",
            parameters={"reason": "Request not recognized or outside allowed scope"},
            description="Abstain from unclear request"
        )
    
    async def execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Execute the specified tool call"""
        try:
            if tool_call.name == "get_run_status":
                return await self._get_run_status(tool_call.parameters["run_id"])
            elif tool_call.name == "run_sensitivity":
                return await self._run_sensitivity(
                    tool_call.parameters["run_id"],
                    tool_call.parameters["shock_type"],
                    tool_call.parameters["shock_value"]
                )
            elif tool_call.name == "explain_run":
                return await self._explain_run(tool_call.parameters["run_id"])
            elif tool_call.name == "abstain":
                return await self._abstain(tool_call.parameters["reason"])
            else:
                return {"error": f"Unknown tool: {tool_call.name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def _get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get run status from API"""
        try:
            response = requests.get(f"http://127.0.0.1:9000/runs/{run_id}")
            if response.status_code == 200:
                run_data = response.json()
                return {
                    "success": True,
                    "data": {
                        "run_id": run_data.get("id"),
                        "status": run_data.get("status"),
                        "created_at": run_data.get("created_at"),
                        "updated_at": run_data.get("updated_at"),
                        "error_message": run_data.get("error_message"),
                        "approach": run_data.get("request", {}).get("approach", []),
                        "instrument_type": "IRS" if "payFixed" in run_data.get("request", {}).get("spec", {}) else "CCS"
                    }
                }
            else:
                return {"success": False, "error": f"Run not found: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to get run status: {str(e)}"}
    
    async def _run_sensitivity(self, run_id: str, shock_type: str, shock_value: float) -> Dict[str, Any]:
        """Run sensitivity analysis"""
        try:
            # Create sensitivity request
            sensitivity_request = {
                "shock_type": shock_type,
                "shock_value": shock_value
            }
            
            response = requests.post(
                f"http://127.0.0.1:9000/runs/{run_id}/sensitivities",
                json=sensitivity_request
            )
            
            if response.status_code == 200:
                sensitivity_data = response.json()
                return {
                    "success": True,
                    "data": {
                        "shock_type": shock_type,
                        "shock_value": shock_value,
                        "pv_delta": sensitivity_data.get("pv_delta", 0),
                        "components": sensitivity_data.get("components", {}),
                        "generated_at": sensitivity_data.get("generated_at")
                    }
                }
            else:
                return {"success": False, "error": f"Sensitivity analysis failed: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to run sensitivity: {str(e)}"}
    
    async def _explain_run(self, run_id: str) -> Dict[str, Any]:
        """Get explanation using RAG"""
        try:
            response = requests.get(f"http://127.0.0.1:8000/explain/{run_id}")
            if response.status_code == 200:
                explanation_data = response.json()
                return {
                    "success": True,
                    "data": {
                        "explanation": explanation_data.get("explanation", ""),
                        "confidence_score": explanation_data.get("confidence_score", 0),
                        "has_sufficient_policy": explanation_data.get("has_sufficient_policy", False),
                        "citations": explanation_data.get("citations", []),
                        "generated_at": explanation_data.get("generated_at")
                    }
                }
            else:
                return {"success": False, "error": f"Explanation failed: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to get explanation: {str(e)}"}
    
    async def _abstain(self, reason: str) -> Dict[str, Any]:
        """Abstain from request with guidance"""
        return {
            "success": True,
            "abstain": True,
            "message": f"I cannot fulfill this request: {reason}. I can only help with: getting run status, running sensitivity analysis, and explaining valuations using our policy documents.",
            "guidance": "Try asking: 'Show me the run status', 'Run parallel +1bp sensitivity', or 'Explain this valuation'."
        }
    
    def format_response(self, tool_call: ToolCall, result: Dict[str, Any]) -> str:
        """Format the tool result into a user-friendly response"""
        if result.get("abstain"):
            return result["message"]
        
        if not result.get("success"):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        data = result.get("data", {})
        
        if tool_call.name == "get_run_status":
            status = data.get("status", "unknown")
            approach = data.get("approach", [])
            instrument_type = data.get("instrument_type", "Unknown")
            
            response = f"**Run Status:** {status}\n"
            response += f"**Instrument Type:** {instrument_type}\n"
            response += f"**Approach:** {', '.join(approach)}\n"
            
            if data.get("error_message"):
                response += f"**Error:** {data['error_message']}\n"
            
            return response
        
        elif tool_call.name == "run_sensitivity":
            shock_type = data.get("shock_type", "unknown")
            shock_value = data.get("shock_value", 0)
            pv_delta = data.get("pv_delta", 0)
            
            response = f"**Sensitivity Analysis Complete**\n"
            response += f"**Shock:** {shock_type} {shock_value:+.1f}bp\n"
            response += f"**PV Delta:** {pv_delta:,.2f}\n"
            
            components = data.get("components", {})
            if components:
                response += "**Component Changes:**\n"
                for component, delta in components.items():
                    response += f"  - {component}: {delta:,.2f}\n"
            
            return response
        
        elif tool_call.name == "explain_run":
            explanation = data.get("explanation", "")
            confidence = data.get("confidence_score", 0)
            citations = data.get("citations", [])
            
            response = f"**Valuation Explanation**\n"
            response += f"**Confidence:** {confidence:.1%}\n\n"
            response += f"{explanation}\n\n"
            
            if citations:
                response += "**Policy References:**\n"
                for i, citation in enumerate(citations, 1):
                    doc_name = citation.get("doc_name", "Unknown")
                    section_id = citation.get("section_id", "Unknown")
                    paragraph_id = citation.get("paragraph_id", "Unknown")
                    relevance = citation.get("relevance_score", 0)
                    response += f"{i}. {doc_name} - {section_id}.{paragraph_id} ({relevance:.1%} relevant)\n"
            
            return response
        
        return "Response generated successfully."
    
    async def process_message(self, message: str, run_id: str) -> Dict[str, Any]:
        """Process a user message and return response"""
        # Parse the message to determine tool call
        tool_call = self.parse_tool_request(message, run_id)
        
        if not tool_call:
            return {
                "error": "Could not parse request",
                "message": "I didn't understand your request. Try asking about run status, sensitivity analysis, or explanations."
            }
        
        # Execute the tool
        result = await self.execute_tool(tool_call)
        
        # Format response
        response_text = self.format_response(tool_call, result)
        
        return {
            "tool_call": tool_call.name,
            "tool_parameters": tool_call.parameters,
            "result": result,
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global agent instance
chat_agent = ConstrainedChatAgent()

