import re
from typing import Any, Dict, Optional

from llama_index.llms.openai_like import OpenAILike

from src.config import get_config
from src.mcp.context import get_repository
from src.mcp.utils.circuit_breaker import cypher_generation_breaker, with_circuit_breaker
from src.mcp.utils.prompt_templates import (
    DEFAULT_TEMPLATE,
    MULTI_REPO_TEMPLATE,
    get_prompt_template,
)
from src.mcp.utils.query_guardrails import enforce_limit
from src.mcp.utils.tracing import get_langfuse

DETERMINISTIC_TOOLS = [
    "find_dependencies",
    "trace_variable",
    "get_role_usage",
    "analyze_playbook",
    "find_tasks_by_module",
    "get_task_hierarchy",
    "find_template_usage",
]


class GraphRAGClient:
    def __init__(self) -> None:
        config = get_config()
        self.llm = OpenAILike(
            model=config.llm.model_name,
            api_base=config.llm.api_base,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            api_key=config.llm.api_key,
            is_chat_model=True,
        )

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        nodes = schema.get("nodes", {})
        rels = schema.get("relationships", {})

        lines = ["Nodes:"]
        for node, details in nodes.items():
            props = ", ".join([p["name"] for p in details.get("properties", [])])
            lines.append(f"  (:{node}) {{ {props} }}")

        lines.append("\nRelationships:")
        for rel, details in rels.items():
            props = ", ".join([p["name"] for p in details.get("properties", [])])
            lines.append(f"  -[:{rel}]-> {{ {props} }}")

        return "\n".join(lines)

    @with_circuit_breaker(cypher_generation_breaker, suggested_tools=DETERMINISTIC_TOOLS)
    async def generate_cypher(self, question: str, repository_id: Optional[str] = None) -> str:
        config = get_config()
        schema_str = self._format_schema(config.schema)
        repo = repository_id or get_repository()

        if repo:
            template = MULTI_REPO_TEMPLATE
            prompt = template.format(schema_str=schema_str, question=question, repository_id=repo)
        else:
            # Fallback to configured or default
            if config.llm.prompt_template != "default":
                template = get_prompt_template(config.llm.prompt_template)
            else:
                template = DEFAULT_TEMPLATE
            prompt = template.format(schema_str=schema_str, question=question)

        langfuse = get_langfuse()
        trace = None
        generation = None
        if langfuse:
            trace = langfuse.trace(name="cypher_generation")
            generation = trace.generation(
                name="cypher_generation",
                model=config.llm.model_name,
                input=prompt,
                metadata={"question": question},
            )

        try:
            response = await self.llm.acomplete(prompt)
            text = response.text

            if generation:
                generation.update(
                    output=text,
                    usage_details={
                        "total_tokens": getattr(response, "total_tokens", 0),
                        "prompt_tokens": getattr(response, "prompt_tokens", 0),
                        "completion_tokens": getattr(response, "completion_tokens", 0),
                    },
                )
                generation.end()
        except Exception as e:
            if generation:
                generation.update(level="ERROR", status_message=str(e))
                generation.end()
            raise

        # Remove <think> tags if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Remove markdown
        text = re.sub(r"```cypher", "", text)
        text = re.sub(r"```", "", text)

        return enforce_limit(text.strip())
