# ruff: noqa
import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.environment import LocalEnvironment
from google.adk.models.registry import LLMRegistry
from google.adk.skills import load_skill_from_dir
from google.adk.tools.environment import EnvironmentToolset
from google.adk.tools.skill_toolset import SkillDiscoveryMode, SkillToolset

# Suporte multiprovedor (Gemini nativo, OpenRouter via LiteLLM, etc.)
RAW_MODEL = os.getenv("MODEL", "gemini-3.5-flash")
if (
    os.getenv("OPENROUTER_API_KEY")
    and "/" in RAW_MODEL
    and not RAW_MODEL.startswith("openrouter/")
):
    MODEL = f"openrouter/{RAW_MODEL}"
else:
    MODEL = RAW_MODEL

# Caminhos absolutos calculados a partir de agent.py
PLANOS_DIR = (Path(__file__).parent.parent / "planos").resolve()
PLANOS_DIR.mkdir(parents=True, exist_ok=True)

SKILL_DIR = (Path(__file__).parent / "skills" / "plano-de-estudos").resolve()


class FerramentasDeArquivo(EnvironmentToolset):
    """Toolset de ambiente restrito para operações de arquivo (ReadFile e WriteFile)."""

    async def get_tools(self, readonly_context=None):
        tools = await super().get_tools(readonly_context)
        return [t for t in tools if t.name in ("ReadFile", "WriteFile")]


def get_instruction(context: ReadonlyContext | None = None) -> str:
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    return (
        f"A data de hoje é {hoje}.\n\n"
        "Você é um mentor especialista em organização e planejamento de estudos.\n"
        "Seu papel é criar e gerenciar planos de estudo personalizados e executáveis utilizando a skill 'plano-de-estudos'.\n\n"
        "Diretrizes fundamentais:\n"
        "1. Regra de Ativação (Gating Rule): Antes de carregar referências ou templates da skill com 'load_skill_resource', "
        "certifique-se de que a conversa possui TODAS as 4 informações obrigatórias: objetivo (o que quer aprender e para quê), "
        "prazo (data de início e data-alvo), disponibilidade (dias da semana e horas por dia) e nível atual no assunto.\n"
        "Se faltar qualquer informação, faça UMA ÚNICA mensagem curta e objetiva pedindo APENAS o que falta, "
        "sem carregar recursos adicionais.\n"
        "2. Com todas as informações em mãos, carregue 'references/workflow.md' através de 'load_skill_resource' e "
        "siga estritamente os passos até a conclusão do plano no formato do template.\n"
        "3. Salve a agenda de estudos gerada no arquivo 'plano-de-estudos.csv' utilizando a ferramenta 'WriteFile'. "
        "Após salvar com sucesso, forneça obrigatoriamente o link de download direto no seguinte formato Markdown: "
        "🔗 [Clique aqui para baixar seu plano-de-estudos.csv](/download/plano-de-estudos.csv) para que a pessoa possa salvar no computador com um clique.\n"
        "4. Em replanejamentos (sessões perdidas), leia o plano anterior com 'ReadFile', recalcule as datas redistribuindo "
        "as sessões sem sobrecarregar um único dia e sobrescreva 'plano-de-estudos.csv' com 'WriteFile'.\n"
        "5. Responda sempre em português do Brasil com tom encorajador, direto e sem enrolação."
    )


# Carrega a skill do plano de estudos
skill_plano = load_skill_from_dir(SKILL_DIR)
skill_toolset = SkillToolset(
    skills=[skill_plano],
    discovery_mode=SkillDiscoveryMode.EAGER,
    tool_filter=["load_skill", "load_skill_resource"],
)

# Ferramentas de arquivo restritas a ReadFile e WriteFile
arquivo_toolset = FerramentasDeArquivo(
    environment=LocalEnvironment(working_dir=PLANOS_DIR)
)

root_agent = Agent(
    name="agente_estudos",
    model=LLMRegistry.new_llm(MODEL),
    instruction=get_instruction,
    tools=[skill_toolset, arquivo_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
