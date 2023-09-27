from dataclasses import dataclass
import json
from langchain.llms import HuggingFacePipeline
from typing import List

from llm.llama import Llama
from llm.gen_chains.suspect_chain import SuspectChain
from llm.gen_chains.victim_chain import VictimChain
from llm.gen_chains.rooms_chain import RoomsChain

@dataclass
class Room:
    name: str
    description: str

@dataclass
class Suspect:
    name: str
    age: int
    occupation: str
    is_guilty: bool
    motive: str
    alibi: str

@dataclass
class Victim:
    name: str
    age: int
    occupation: str
    murder_weapon: str
    death_description: str

@dataclass
class Story:
    theme: str
    victim: Victim
    suspects: List[Suspect]
    rooms: List[Room]

class LlmStoryGenerator:
    def __init__(self, rooms_layout):
        llama_pipeline = Llama().pipeline
        self._llm = HuggingFacePipeline(pipeline=llama_pipeline)
        
        self._rooms_layout = rooms_layout
    
    def create_new_story(self, theme: str, dummy: bool = False) -> Story:
        if dummy:
            with open("./llm-dungeon-adventures/data/dummy.json", 'r') as f:
                return json.load(f)


        victim = VictimChain(self._llm).create(theme)
        suspects = SuspectChain(self._llm).create(theme, victim)
        rooms = RoomsChain(self._llm, self._rooms_layout).create(theme, victim, suspects)

    
        return {
            "theme": theme,
            "victim": victim,
            "suspects": suspects,
            "rooms": rooms
        }