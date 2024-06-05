import sys
import argparse
import logging

from llmtool.interactive_markdown import (
    MarkdownDocument,
    CodeBlock,
    SyntaxHighlightingError,
)

from llmtool.patch import apply_patch

from llmtool.genai.agent import Agent


def get_message(cli_args) -> str:
    if cli_args.stdin:
        return sys.stdin.read().strip()
    else:
        # exit with error if message not given on stdin
        if not cli_args.message:
            sys.exit("Must give message via stdin or argv")
        # read file from argv
        return cli_args.message


class ReplyPresenter:
    def __init__(
        self, reply: str, interactive: bool = False, skip_styling: bool = False
    ):
        self.reply = reply
        self.interactive = interactive
        self.skip_styling = skip_styling

    def present(self):
        if self.interactive:
            self.present_interactive()
        else:
            if sys.stdout.isatty() and not self.skip_styling:
                self.present_highlighted()
            else:
                self.present_raw()

    def present_interactive(self):
        doc = MarkdownDocument(self.reply)
        for node in doc.get_nodes():
            if isinstance(node, CodeBlock):
                sys.stdout.write(node.to_highlighted_string())

                if node.language == "diff":
                    response = input("apply diff? (y/n)")
                    if response.strip() == "y":
                        apply_patch(node.code)

                if node.language == "sh":
                    response = input("execute shell command? (y/n)")
                    if response.strip() == "y":
                        os.system(node.code)
            else:
                sys.stdout.write(node.raw())

    def present_highlighted(self):
        markdown_document = MarkdownDocument(self.reply)
        try:
            print(markdown_document.to_highlighted_string())
        except SyntaxHighlightingError as e:
            print("Syntax Highlighting Error: " + str(e), file=sys.stderr)
            self.present_raw()

    def present_raw(self):
        print(self.reply)


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-s",
        "--stdin",
        help="read message from stdin",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-m", "--model", type=str, help="GPT model to use", default="gpt-4-1106-preview"
    )
    parser.add_argument(
        "-c", "--conversation", type=str, help="conversation name", default="default"
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        help="maximum token count threshold",
        default=8000,
    )
    parser.add_argument(
        "-i",
        "--interactive",
        help="interactive mode",
        default=False,
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--retrieve-last",
        help="retrieve last message in this convo",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--get-token-count",
        help="get token count of this convo",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--skip-styling",
        help="skip syntax highlighting",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--disable-functions",
        help="disable GPT functions",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-v", "--verbose", help="verbose logging", required=False, action="store_true"
    )
    parser.add_argument("message", type=str, help="message to send to GPT-3", nargs="?")
    args = parser.parse_args()

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stderr))
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    agent = Agent(
        args.model, args.conversation, args.threshold, args.disable_functions, logger
    )

    if args.retrieve_last:
        agent.load_chat_history()
        message = agent.chat_history.messages[-1]
        presenter = ReplyPresenter(message.content, args.interactive, args.skip_styling)
        presenter.present()
    if args.get_token_count:
        agent.load_chat_history()
        print(agent.chat_history.get_token_count())
    else:
        message_text = get_message(args)

        # Send message to chat GPT
        reply = agent.send_user_message(message_text)
        presenter = ReplyPresenter(reply.content, args.interactive)
        presenter.present()


if __name__ == "__main__":
    main()
