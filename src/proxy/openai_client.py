import openai
from typing import List

from common.cache import Cache
from common.request import Request, RequestResult, Sequence, Token
from .client import Client


class OpenAIClient(Client):
    def __init__(self, api_key: str, cache_path: str):
        openai.api_key = api_key
        self.cache = Cache(cache_path)

    def make_request(self, request: Request) -> RequestResult:
        raw_request = {
            "engine": request.model_engine(),
            "prompt": request.prompt,
            "temperature": request.temperature,
            "n": request.num_completions,
            "max_tokens": request.max_tokens,
            "best_of": request.top_k_per_token,
            "logprobs": request.top_k_per_token,
            "stop": request.stop_sequences or None,  # API doesn't like empty list
            "top_p": request.top_p,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
            "echo": request.echo_prompt,
        }

        try:

            def do_it():
                return openai.Completion.create(**raw_request)

            response, cached = self.cache.get(raw_request, self.wrap_request_time(do_it))
        except openai.error.InvalidRequestError as e:
            return RequestResult(success=False, cached=False, error=str(e), completions=[])

        completions = []
        for raw_completion in response["choices"]:
            sequence_log_prob = 0
            tokens: List[Token] = []

            raw_data = raw_completion["logprobs"]
            for text, log_prob, top_choices in zip(raw_data["tokens"], raw_data["token_logprobs"], raw_data["top_logprobs"]):
                # For some reason, the first log probability and top choices are None.
                # TODO: look in to why this is
                tokens.append(Token(text=text, log_prob=log_prob or 0, top_choices=dict(top_choices or {})))
                sequence_log_prob += log_prob or 0
            completion = Sequence(text=raw_completion["text"], log_prob=sequence_log_prob, tokens=tokens)
            completions.append(completion)
        return RequestResult(
            success=True, cached=cached, request_time=response["request_time"], completions=completions
        )
