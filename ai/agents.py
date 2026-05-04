import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json
from dotenv import load_dotenv

#loading openai api key
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



def is_youtube_video():
    #ask ai to know if there is a clip else return null/none
    return
