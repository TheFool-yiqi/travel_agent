"""Greeting-only first-turn handling for collect."""

from __future__ import annotations

from app.graph.greeting import build_greeting_reply, is_greeting_only_text


class GreetingPolicy:
    @staticmethod
    def is_greeting_only(user_message: str) -> bool:
        return is_greeting_only_text(user_message)

    @staticmethod
    def should_greet(*, user_message: str, has_prior_assistant_message: bool) -> bool:
        return is_greeting_only_text(user_message) and not has_prior_assistant_message


class GreetingResponder:
    @staticmethod
    def build_reply(*, already_greeted: bool = False) -> str:
        if already_greeted:
            return "你好！咱们继续吧——你想去哪里玩呢？"
        return build_greeting_reply()
