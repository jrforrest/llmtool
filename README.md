# LLMTool

My Command-line tool for interracting with LLMs.  Currently supports LLaMA and GPT.

This is a prototype-grade personal tool and is not maintained for public use.
There are better-maintained tools available out there since I built this.

## Usage

```shell
export OPENAPI_TOKEN=<token>
llmtool 'Read me a bedtime story please.'
```

Input can be read from STDIN

```
cat <<EOF
I have this rust code:

$(cat src/main.rs)

Tell me why it results in these build errors:

$(cargo build 2>&1)
EOF | llmtool -s
```

If a postgres connection is provided, the tool will utilized vector indices to store and retrieve
notes.  This is only available with OpenAI GPT models since it requires use of function calls.

Shell scripts can also be run directly from responses with GPT function calls.
