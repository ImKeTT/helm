from typing import List

from .client import Client
from common.request import Request, RequestResult, Sequence, Token


class SimpleClient(Client):
    """Implements some "models" that just generate silly things quickly just to debug the infrastructure."""

    def make_request(self, request: Request) -> RequestResult:
        if request.model == "simple/model1":
            completions = self.invoke_model1(request)
        else:
            raise ValueError("Unknown model")
        return RequestResult(
            success=True,
            cached=False,
            request_time=0,
            completions=completions,
        )

    def invoke_model1(self, request: Request) -> List[Sequence]:
        """
        Example: 7 2 4 6
        Completions (num_completions = 3):
        - 6
        - 4
        - 2
        """
        prompt_tokens = request.prompt.split(" ")

        choices = reversed(prompt_tokens[-request.num_completions :])
        top_choices = dict((text, -i) for i, text in enumerate(choices))

        return [
            Sequence(
                text=text, log_prob=log_prob, tokens=[Token(text=text, log_prob=log_prob, top_choices=top_choices)]
            )
            for text, log_prob in top_choices.items()
        ]
