from client import RNCClient
from config import Config


class CorpusResourceGenerator:
    def __init__(self, client: RNCClient):
        self.client = client

    async def generate(self, corpus: str) -> str:
        """
        Generates a Markdown description of the corpus configuration,
        including sorting methods, filters, and grammatical tags.
        """
        try:
            Config.get_token()

            # Fetch Data
            config_data = await self.client.get_corpus_config(corpus)
            gramm_data = await self.client.get_grammar_attributes(corpus)

            output = [f"# Configuration for {corpus}\n"]

            # Sorting
            output.append("## Available Sorting Methods")
            sortings = config_data.get("sortings", [])
            valid_sorts = [
                s for s in sortings
                if "CONCORDANCE" in s.get("applicableTo", [])
            ]

            if not valid_sorts:
                output.append("_No sorting methods available._")
            else:
                for s in valid_sorts:
                    name = s.get("name")
                    readable = s.get("humanReadable")
                    line = f"- `{name}`"
                    if readable:
                        line += f" ({readable})"
                    output.append(line)

            # Filters
            output.append("\n## Filter Fields")
            stats_fields = config_data.get("statFields", [])
            if not stats_fields:
                output.append("_No filter fields available._")
            else:
                for f in stats_fields:
                    output.append(f"- `{f}`")

            # Grammar Tags
            output.append("\n## Grammar Tags (attr: 'gramm')")

            vals = gramm_data.get("vals", [])
            if not vals:
                output.append("_No grammar tags found._")
            else:
                for val in vals:
                    root_options = val.get(
                        "valOptions",
                        {}).get(
                        "v",
                        {}).get(
                        "options",
                        [])
                    output.append(self._format_options(root_options))

            return "\n".join(output)

        except Exception as e:
            return f"Error loading resource for {corpus}: {str(e)}"

    def _format_options(self, options, level=0) -> str:
        res = ""
        indent = "  " * level
        for opt in options:
            title = opt.get("title")
            val = opt.get("value")
            sub = opt.get("suboptions", {}).get("options", [])

            if sub:
                res += f"\n{indent}- **{title}**\n"
                res += self._format_options(sub, level + 1)
            elif val:
                res += f"{indent}- `{val}` ({title})\n"
        return res
