from collections import deque
import json
from langchain.prompts import PromptTemplate

from environment.types import Grid
from llm.output_parsers.room import RoomYamlOutputParser

class RoomsChain:
    def __init__(self, llm, rooms: Grid) -> None:
        self._llm = llm

        self._rooms = rooms
        self._rows, self._columns = len(rooms), len(rooms[0])

        self._suspect_room_prompt = PromptTemplate.from_template(
            """
            <s>[INST] <<SYS>>
            You are a crime storyteller.
            <<SYS>>

            Describe a room given a theme and information about a suspect person in that room.
            Room is described by its name and a description.
            An example is below. Note that you must output only created description converted to YAML where all properties are on same level.
            
            Example answer:
            room:
              name: "The Ancient Manuscript Chamber"
              description: "Ancient Manuscript Chamber is known as the Preservation Gallery. It serves as a critical space for the maintenance and restoration of the library's valuable scrolls and manuscripts. The room is well-lit with natural sunlight streaming in through high windows, revealing a contrast to the dimly lit chamber next door. Large, polished wooden tables occupy the center of the room, where scholars and assistants like Lucius meticulously repair and transcribe ancient texts. Rows of neatly organized shelves hold scrolls in protective containers. The air in this room carries the faint aroma of aged parchment and the careful attention of those dedicated to preserving the knowledge of the ages. Lucius, the Librarian's Assistant, was seen in this room working diligently during the time of Drusilla's murder, and he claims he had no involvement in the crime." [/INST]
            
            Give the output for the following theme: {theme} and suspect: {entity}
            """
        )

        self._victim_room_prompt = PromptTemplate.from_template(
            """
            <s>[INST] <<SYS>>
            You are a crime storyteller.
            <<SYS>>

            Describe a room where the body was found given a theme and information about the victim.
            Room is described by its name and a description.
            An example is below. Note that you must output only created description converted to YAML where all properties are on same level.
            
            Example answer:
            room:
              name: "The Ancient Manuscript Chamber"
              description: "The room where Drusilla's lifeless body was discovered is known as the Ancient Manuscript Chamber. It is a dimly lit and secluded section of the library, hidden away from the bustling main halls. The chamber is lined with tall, dusty bookshelves filled with scrolls and manuscripts dating back centuries. The air is heavy with the scent of aging parchment and the mustiness of forgotten knowledge. Dim torches cast flickering shadows on the ancient tomes, creating an eerie ambiance. The room is a labyrinth of knowledge, and it was amidst this maze of scrolls and manuscripts that Drusilla met her tragic end, stabbed multiple times with an ancient dagger." [/INST]
            
            Give the output for the following theme: {theme} and victim: {entity}
            """
        )

    def create(self, theme, victim, suspects):
        # generate description for the starting room, assumes square rooms layout
        middle_row, middle_col = self._rows // 2, self._columns // 2
        start_story = self.generate_room(self._victim_room_prompt, theme, json.dumps(victim))
        start_story.update({"row": middle_row, "col": middle_col})

        # contains final description of rooms
        rooms_data, suspects_positions = [start_story], []

        # generate rest of the rooms
        not_selected_suspects = deque(suspects)
        generated = set([(middle_row, middle_col)])
        q = deque(self._get_neighbours(middle_row, middle_col))
        while q:
            current_room = q.pop()
            if current_room in generated:
                continue

            row, col = current_room

            current_room_story = self.generate_room(
                self._suspect_room_prompt, theme, json.dumps(not_selected_suspects.popleft())
            )
            current_room_story.update({"row": row, "col": col})
            rooms_data.append(current_room_story)

            generated.add((row, col))
            q.extend(self._get_neighbours(row, col))
            suspects_positions.append({"row": row, "col": col})

        return rooms_data, suspects_positions

    def generate_room(self, prompt, theme, entity):
        chain = prompt | self._llm | RoomYamlOutputParser()
        return chain.invoke({"theme": theme, "entity": entity})

    def _get_neighbours(self, row, col):
        neighbours = []
        for x, y in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            if (
                0 <= row + x < self._rows
                and 0 <= col + y < self._columns
                and self._rooms[row + x][col + y]
            ):
                neighbours.append((row + x, col + y))

        return neighbours
