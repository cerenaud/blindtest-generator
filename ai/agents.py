import os
from pprint import pprint
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json
from dotenv import load_dotenv

# Remplacez "<votre_cle_openai>" par votre clé API OpenAI
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class Songs(BaseModel):
    name: str = Field(description="Nom de la chanson")
    artist: str = Field(description="Artiste")
    release_year: int = Field(description="Année de sortie")
    id: int=Field(description="Ne pas changer)")


class SongsOutput(BaseModel):
    songs: List[Songs] = Field(description="Liste des chansons")

def correct_release_year(data: dict)  :
    # Création du model LangChain OpenAI chat
    model = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        #max_tokens=500
    )

    # Création du prompt
    # prompt_template = PromptTemplate.from_template(
    #     "Tu es un expert en musique qui doit corriger les dates de sortie de musique dans un dict python et le renvoyer sans autre messages. "
    #     "Remplace les dates de sorties qui sont fausses par les bonnes dans {data}?"
    # )
    # prompt = prompt_template.format(data=data)

    structured_llm = model.with_structured_output(SongsOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu es un expert en musique. Corrige les années."
         "Corrige les années de sortie des chansons si elles sont incorrectes. "
         "Retourne uniquement les données structurées."),
        ("human",
         "Voici un dict à corriger :\n{input}")
    ])

    chain = prompt | structured_llm

    return chain.invoke({
        "input": json.dumps(data)
    })

    # Appel de l'API OpenAI
    ai_response = model.invoke(prompt)
    return ai_response.content

# data = {
#   "songs": [
#     {
#       "name": "Hotel California",
#       "artist": "Eagles",
#       "release_year": 2019
#     },
#     {
#       "name": "Come as you are",
#       "artist": "Nirvana",
#       "release_year": 1992
#     },
#     {
#       "name": "One More Time",
#       "artist": "Daft Punk",
#       "release_year": 2018
#     },
#     {
#       "name": "Lose Yourself",
#       "artist": "Eminem",
#       "release_year": 2003
#     }
#   ]
# }
#
# data["songs"].append({
#     "name": "Feel Good Inc.",
#     "artist": "Black Sabbath",
#     "release_year": 1999
# })

# test = correct_release_year(data)
# test = test.model_dump()
# print(test)
# print(type(test))
# print(test["songs"][0]["release_year"])

