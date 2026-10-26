from types import SimpleNamespace

from app import ask as ask_module


def test_chat_keeps_history_prints_usage_and_exits_on_blank(monkeypatch, capsys):
    class FakeConversation:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(
                text=f"answer: {question}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=10,
                    candidates_token_count=5,
                ),
            )

    conversation = FakeConversation()

    class FakeChats:
        def create(self, model):
            return conversation

    class FakeClient:
        def __init__(self, api_key):
            self.chats = FakeChats()

    monkeypatch.setattr(ask_module.genai, "Client", FakeClient)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    questions = iter(["follow up", "  "])
    monkeypatch.setattr("builtins.input", lambda _: next(questions))

    ask_module.chat("first question")

    output = capsys.readouterr().out
    assert conversation.questions == ["first question", "follow up"]
    assert output.count("[トークン]") == 2
    assert "answer: first question" in output
    assert "answer: follow up" in output


def test_main_uses_chat_only_when_requested(monkeypatch):
    calls = []
    monkeypatch.setattr(ask_module, "ask", lambda question: calls.append(("ask", question)) or "answer")
    monkeypatch.setattr(ask_module, "chat", lambda question=None: calls.append(("chat", question)))
    monkeypatch.setattr("sys.argv", ["app.ask"])

    ask_module.main()
    monkeypatch.setattr("sys.argv", ["app.ask", "--chat"])
    ask_module.main()

    assert calls == [
        ("ask", ask_module.DEFAULT_QUESTION),
        ("chat", None),
    ]