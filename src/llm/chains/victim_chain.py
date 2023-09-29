import json
from langchain.prompts import PromptTemplate

from llm.output_parsers.victim import VictimYamlOutputParser


class VictimChain:
    def __init__(self, llm):
        self._json_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "occupation": {"type": "string"},
                "murder_weapon": {"type": "string"},
                "death_description": {"type": "string"},
            },
            "required": [
                "name",
                "age",
                "occupation",
                "murder_weapon",
                "death_description",
            ],
        }

        self._one_shot_example = {
            "name": "Archibald Ptolemy",
            "age": 42,
            "occupation": "Head librarian",
            "murder_weapon": "fragile ancient scroll",
            "death_description": "Found face down under pile of books with a broken quill pen lodged in his back, surrounded by scattered papyrus rolls."   
        }

        self._prompt = PromptTemplate.from_template(
            """
            <s>[INST] <<SYS>>
            
            You are a crime storyteller. Always output answer as JSON using this {scheme}.
            Avoid outputting anything else than the JSON answer.
            Avoid providing nicknames for people, places, etc..
                        
            <<SYS>>

            Given a theme: "Library of Alexandria, 340 BC, crazy librarian" describe a victim of the story.
            victim:
            [/INST]
            {one_shot_example}</s><s>
            
            [INST]
            Given a theme: {theme} describe a victim of the story.
            victim:
            [/INST]
            """
        )

        self._chain = self._prompt | llm# | VictimYamlOutputParser()

    def create(self, theme):
        return self._chain.invoke(
            {
                "one_shot_example": json.dumps(self._one_shot_example),
                "scheme": json.dumps(self._json_schema),
                "theme": theme,
            }
        )
