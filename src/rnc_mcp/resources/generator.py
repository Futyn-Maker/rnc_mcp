from rnc_mcp.client import RNCClient
from rnc_mcp.config import Config


class RNCResourceGenerator:
    def __init__(self, client: RNCClient):
        self.client = client

    async def generate(self, corpus: str) -> str:
        """
        Generates a Markdown description of the corpus configuration,
        including sorting methods and all attribute types.
        """
        try:
            Config.get_token()

            # Fetch Data
            config_data = await self.client.get_corpus_config(corpus)

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

            # Fetch all attribute types
            attr_types = [
                ("gr", "Grammar Tags (attr: 'gramm')"),
                ("sem", "Semantic Tags (attr: 'semantic')"),
                ("syntax", "Syntax Tags (attr: 'syntax')"),
                ("flags", "Additional Flags (attr: 'flags')")
            ]

            for attr_type, title in attr_types:
                try:
                    attr_data = await self.client.get_attributes(
                        corpus, attr_type
                    )
                    output.append(f"\n## {title}")

                    vals = attr_data.get("vals", [])
                    if not vals:
                        output.append(f"_No {attr_type} tags found._")
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
                except Exception:
                    output.append(f"_No {attr_type} tags available._")

            return "\n".join(output)

        except Exception as e:
            return f"Error loading resource for {corpus}: {str(e)}"

    def _format_options(self, options, level=0) -> str:
        """
        Format attribute options into markdown.
        Handles nested structures where nodes can have both values
        and suboptions.
        """
        res = ""
        indent = "  " * level
        for opt in options:
            title = opt.get("title")
            val = opt.get("value")
            sub = opt.get("suboptions", {}).get("options", [])

            if val and sub:
                # Node has both value and suboptions
                res += f"{indent}- `{val}` (**{title}**)\n"
                res += self._format_options(sub, level + 1)
            elif val:
                # Node has only value (leaf node)
                res += f"{indent}- `{val}` ({title})\n"
            elif sub:
                # Node has only suboptions (category header)
                res += f"\n{indent}- **{title}**\n"
                res += self._format_options(sub, level + 1)
            else:
                # Node has only title (shouldn't happen normally)
                res += f"{indent}- {title}\n"
        return res
