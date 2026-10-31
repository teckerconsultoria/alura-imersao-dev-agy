import datetime
import pytest
from app.agent import app, root_agent


def test_agent_configuration():
    assert root_agent.name == "agente_estudos"
    assert app.name == "app"
    assert app.root_agent is root_agent


def test_agent_instruction_contains_current_date():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    instruction = root_agent.instruction(None)
    assert today_str in instruction


@pytest.mark.asyncio
async def test_agent_tools_filtered_correctly():
    tool_names = []
    for tool in root_agent.tools:
        if hasattr(tool, "get_tools"):
            sub_tools = await tool.get_tools()
            tool_names.extend([t.name for t in sub_tools])
        else:
            tool_names.append(getattr(tool, "name", str(tool)))

    # Deve conter exatamente as ferramentas autorizadas
    assert set(tool_names) == {"load_skill", "load_skill_resource", "ReadFile", "WriteFile"}
    # Não deve expor comandos de shell
    assert "Execute" not in tool_names
    assert "EditFile" not in tool_names
