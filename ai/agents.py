import os
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json
from dotenv import load_dotenv

#loading openai api key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

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


#this approach doesn't seems to work because these models can't give
#the right url
class YoutubeClipOutput(BaseModel):
    youtube_url: Optional[str] = Field(
        description="Lien YouTube du clip officiel s'il existe, sinon None"
    )

def is_youtube_video(title: str, artist: str):
    #ask ai to know if there is a clip else return null/none
    # Création du model LangChain OpenAI chat
    model = ChatOpenAI(
        #model_name="gpt-4o-mini",
        model="gpt-5.3-codex",
        temperature=0,
        # max_tokens=500
    )

    structured_llm = model.with_structured_output(YoutubeClipOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu es un expert en musique et en clip video officiel des musiques."
         "A partir d'un titre de musique et d'un artiste, répond si il existe un clip video connu de la musique. "
         "Retourne uniquement en envoyant le lien YouTube s'il existe ou sinon None."),
        ("human",
         "Voici une musique dont on cherche a trouver le lien YouTube du clip s'il existe:\n{title} - {artist}")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "title": title,
        "artist": artist
    })

    return result.youtube_url

# test = is_youtube_video("All alone","Gorillaz")
# print(test)

#We'll give direectly the url (fetched from yt-dlp) and ask if it is officle or relevant
class IsYoutubeClipOutput(BaseModel):
    answer: str = Field(description="Réponse s'il existe un clip video")

def is_youtube_video_from_url(title: str, artist: str, url: str):
   # Création du model LangChain OpenAI chat
    model = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        # max_tokens=500
    )

    structured_llm = model.with_structured_output(IsYoutubeClipOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu es un expert en musique et en clip video officiel des musiques."
         "A partir d'un titre de musique,d'un artiste et d'une url YouTube, répond si l'url contient un clip video officiel ou pertinent "
         "Retourne uniquement en disant Yes ou No."),
        ("human",
         "Voici une musique dont on cherche a savoir si le lien YouTube est un clip pertinent/officiel:\n{title} - {artist} - {url}")
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "title": title,
        "artist": artist,
        "url": url
    })

    return result.answer
#rl = "https://www.youtube.com/watch?v=n3_4pMFUctA"
# test = is_youtube_video_from_url("Hotel California","Eagles",url)
# print(test)

class ClipValidationOutput(BaseModel):
    is_official: bool = Field(
        description="True si cette vidéo correspond à un clip officiel ou vidéo officielle pertinente"
    )

def is_official_clip(song_title: str, artist: str) -> bool:
    model = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0
    )

    structured_llm = model.with_structured_output(ClipValidationOutput)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Tu es expert musique. "
            "Détermine si il existe un clip officiel pour une chanson avec un artiste ou non, "
        ),
        (
            "human",
            """Chanson:
Titre: {song_title}
Artiste: {artist}
"""
        )
    ])

    chain = prompt | structured_llm

    result = chain.invoke({
        "song_title": song_title,
        "artist": artist,
    })

    return result.is_official

#print(is_official_clip("All alone", "Gorillaz"))

from openai import OpenAI
client = OpenAI(api_key=openai_api_key)
#oracle
def check_clip(artist, song):
    prompt = f"""
    Existe-t-il un clip officiel pour la chanson "{song}" de {artist} ?
    Réponds uniquement par OUI si et seulement si il existe un clip officiel sinon NON.
    """

    response = client.responses.create(
        model="gpt-5.3-codex",
        input=prompt
    )

    return response.output[0].content[0].text


#print(check_clip("Vald", "Rocking chair"))
#peut etre comparé le lien qu'il fournit