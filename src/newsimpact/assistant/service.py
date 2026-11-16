"""Answer one question: limit -> tools and model -> checks -> answer with its sources."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from newsimpact.assistant.logic import NOT_IN_DATA, SYSTEM, Notebook, split_sources, toolbox
from newsimpact.assistant.models import Answer, AssistantPolicy
from newsimpact.assistant.ports import NewsData, QuestionLog, ToolModel
from newsimpact.llm.models import BudgetExceededError, ToolRequest
from newsimpact.shared.guardrails import grounded

log = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500


class AssistantService:
    def __init__(
        self,
        model: ToolModel | None,
        data: NewsData,
        questions: QuestionLog,
        policy: AssistantPolicy,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._model = model
        self._data = data
        self._questions = questions
        self._policy = policy
        self._now = now

    @property
    def available(self) -> bool:
        return self._model is not None

    def ask(self, user_id: str, question: str, event_id: str | None = None) -> Answer:
        question = " ".join(question.split())[:MAX_QUESTION_CHARS]
        if self._model is None:
            return Answer(question=question, status="unavailable",
                          text="The assistant needs a language model (NI_LLM_PRESET).")  # fmt: skip
        day = self._now().strftime("%Y-%m-%d")
        if self._questions.count(user_id, day) >= self._policy.questions_per_user_per_day:
            return Answer(question=question, status="limit_reached",
                          text=f"Daily limit of {self._policy.questions_per_user_per_day} "
                               "questions reached; it resets tomorrow (UTC).")  # fmt: skip
        notebook = Notebook()
        prompt = question if event_id is None else (
            f"{question}\n(The person is looking at event_id {event_id}.)")  # fmt: skip
        request = ToolRequest(purpose="assistant.ask", system=SYSTEM, prompt=prompt,
                              max_output_tokens=self._policy.max_output_tokens,
                              max_steps=self._policy.max_steps)  # fmt: skip
        try:
            result = self._model.run_tools(request, toolbox(self._data, notebook))
        except BudgetExceededError as exc:
            log.info("assistant skipped: %s", exc)
            return Answer(
                question=question,
                status="unavailable",
                text="The monthly AI budget is used up; answers resume next month.",
            )
        self._questions.add(user_id, day)
        if result is None or not result.text:
            return Answer(question=question, status="unavailable",
                          text="No answer this time (the model stopped before finishing).",
                          tools_used=tuple(notebook.calls))  # fmt: skip
        return self._checked(question, result.text, notebook, result.model, result.cost_usd)

    def _checked(self, question: str, raw: str, notebook: Notebook, model: str,
                 cost: float) -> Answer:  # fmt: skip
        text, urls = split_sources(raw)
        sources = tuple(dict.fromkeys(notebook.links[u] for u in urls if u in notebook.links))
        answer = Answer(question=question, text=text, status="answered", sources=sources,
                        tools_used=tuple(notebook.calls), model=model, cost_usd=cost)  # fmt: skip
        if text.startswith(NOT_IN_DATA):
            return answer.model_copy(update={"status": "not_in_our_data", "sources": ()})
        # Numbers may come from the tools' results or from the question itself ("last 7 days").
        if not grounded(text, "\n".join([*notebook.outputs, question])):
            log.warning("assistant answer failed the checks", extra={"model": model})
            return answer.model_copy(update={
                "status": "checks_failed", "sources": (),
                "text": "No answer shown: NewsImpact states facts, never investment advice, "
                        "and every number must come from our data. Try asking what happened, "
                        "who reported it, or how the stock moved."})  # fmt: skip
        return answer
