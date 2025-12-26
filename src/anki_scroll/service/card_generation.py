from anki_scroll.services import CardGenerator, Card
from anki_scroll.service.website_query import WikipediaIndex, _wikipedia_article
from anki_scroll.llms import grok_fast_no_cache
from dataclasses import dataclass
import dspy
import pydantic



@dataclass(frozen=True)
class CardKey:
    """
    identify a batch of cards
    """
    theme: str
    instructions: str

class LLMCardGeneration(CardGenerator):
    """
    generate flash cards using an llm.
    Cards are generated in batch then stored to be consumed, in order to optimise latency.
    """
    
    def __init__(self, batch_size=20) -> None:
        """
        :param batch_size: size of the batch of cards
        """
        self._batch_size = batch_size
        self._buffer: dict[CardKey, list[Card]] = dict()
        
    def create_card(self, theme: str, instructions: str) -> Card:
        key = CardKey(theme=theme, instructions=instructions)
        
        if len(self._buffer.get(key,[])) == 0:
            self._buffer[key] = _generate_cards(
                theme=theme, 
                instructions=instructions, 
                n=self._batch_size)
        
        return self._buffer[key].pop()
    
    
    

class InsCard(pydantic.BaseModel):
    """
    A flashcard, it contains a question and an answer.
    """
    question: str
    answer: str
    

class CardsFromDocument(dspy.Signature):
    """
    Create n flash cards about a specific theme.
    All the flash cards must be supported by the context documents.
    """
    topic: str = dspy.InputField(desc="topic of the flash cards")
    user_instructions: str = dspy.InputField(desc="instructions to follow when creating the flash cards")
    documents: list[str] = dspy.InputField(desc="documents about the topic")
    n: int = dspy.InputField(desc="number of flash cards to generate")
    flash_cards: list[InsCard] = dspy.OutputField(desc="the list of generated flash cards")
    

def _generate_cards(theme: str, instructions: str, n: int) -> list[Card]:
    search = WikipediaIndex()
    search.set_lm(grok_fast_no_cache)
    
    make_cards = dspy.ChainOfThought(CardsFromDocument)    
    make_cards.set_lm(grok_fast_no_cache)
    
    documents_urls = search.query(query=f"documents about {theme}", limit=2)
    # to do add logging in case of wrong article => directly consume url
    documents = [_wikipedia_article(article=url.url.split("/")[-1]) for url in documents_urls]
    cards = make_cards(topic=theme, user_instructions=instructions, documents=documents, n=n)
    
    return [Card(question=card.question, answer=card.answer) for card in  cards.flash_cards]
        
    