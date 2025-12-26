"""
contain all logic used to train WikipediaIndex search module
"""
from anki_scroll.service.website_query import WikipediaIndex
import dspy
from train.config import data_folder
import json
from pathlib import Path
from gepa.core.adapter import ProposalFn
from dspy.teleprompt.gepa.gepa_utils import ReflectiveExample

query_field = "query"
limit = "limit"
articles_field = "pages"


def load_wikipedia_dataset() -> list[dspy.Example]:
    dataset_path = data_folder / "wikipedia_dataset.json"
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    examples = []
    for item in data:
        example = dspy.Example(
            query=item[query_field],
            limit=len(item[articles_field]),
            pages=item[articles_field]
        ).with_inputs(query_field, limit)
        
        examples.append(example)
    
    return examples



def recall_metric(input: dspy.Example, pred: dspy.Prediction) -> float:
    """input also contain the ground truth"""
    ground_t = input[articles_field]
    retrieved_pages = [Path(url).parts[-1] for url in pred["websites"]]
    
    return len(set(retrieved_pages).intersection(ground_t))/len(ground_t)

class ScoreFeedback(dspy.Prediction):
    score: float
    feedback: str

def recall_feedback(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace = None,
    pred_name = None,
    pred_trace = None) -> ScoreFeedback:
    
    ground_t = set(gold[articles_field])
    retrieved_pages = set([Path(url).parts[-1] for url in pred["websites"]])
    
    most_relevant_articles = ground_t.intersection(retrieved_pages)
    missing_articles = ground_t.difference(retrieved_pages)
    irrelevant = retrieved_pages.difference(ground_t)
    
    feedback = f"""
    for query: {gold[query_field]}
    you retrieved correctly the following wikipedia pages: {', '.join(most_relevant_articles)}
    you did not retrieve the following wikipedia pages: {', '.join(missing_articles)}
    and you retrived the following articles that are not part of the ground truth: {', '.join(irrelevant)}
    """
    
    score = len(most_relevant_articles)/len(ground_t)
    return ScoreFeedback(score=score, feedback=feedback)
    
      

class GenerateInstructionFromFeedback(dspy.Signature):
    """I provided an assistant with instructions to perform a task, but the assistant's performance needs improvement based on the examples and feedback below.

    Your task is to write a better instruction for the assistant that addresses the specific issues identified in the feedback.

    ## Analysis Steps:
    1. **Read the inputs carefully**
    2. **Read all the assistant responses and corresponding feedback** to understand what went wrong
    3. **Identify domain-specific knowledge** as this information may not be available to the assistant in the future

    ## Instruction Requirements:
    - **Clear task definition** explaining how to process textual inputs
    - **Precise, actionable language** for the instructions
    
    ## Constraints:
    - **the instructions should not overfit the examples**: the instructions must not contain examples or psecific knowledge about :
        Cardiac Anatomy
        Organic Chemistry: Alkene Reactions
        Spanish: Irregular Preterite Tense Verbs
        Norse Mythology: The Gods of Asgard
        Renaissance Art: Italian Masters
        Culinary Arts: French Mother Sauces
        Human Anatomy: The Bones of the Cranium
        Astronomy: Planetary Moons
        First Aid: CPR Protocols
        VBA/Excel: Core Functions
        Classical Architecture: Greek Orders
        French: Subjunctive Triggers
        Calculus: Differentiation Rules
    If you want to include examplesyou must create ones about different subjects.
    Your instructions should be less than 750 words.

    """

    current_instruction = dspy.InputField(
        desc="The current instruction that was provided to the assistant to perform the task"
    )
    examples_with_feedback = dspy.InputField(
        desc="Task examples with inputs, assistant outputs, and feedback. "
    )

    improved_instruction = dspy.OutputField(
        desc="A better instruction for the assistant that addresses, provides "
        "clear guidance on how to process"
    )

class CustomInstructionProposer(ProposalFn):
    """GEPA-compatible custom instruction proposer.

    Leverage doamin specific knowledge to regularize the prompt
    """

    def __init__(self):
        self.single_proposer =  dspy.Predict(GenerateInstructionFromFeedback)

    def __call__(
        self,
        candidate: dict[str, str],
        reflective_dataset: dict[str, list[ReflectiveExample]],
        components_to_update: list[str],
    ) -> dict[str, str]:
        """GEPA-compatible proposal function.

        Args:
            candidate: Current component name -> instruction mapping
            reflective_dataset: Component name -> list of reflective examples
            components_to_update: List of component names to update

        Returns:
            dict: Component name -> new instruction mapping
        """
        updated_components = {}

        for component_name in components_to_update:
            if component_name in candidate and component_name in reflective_dataset:
                current_instruction = candidate[component_name]
                component_reflective_data = reflective_dataset[component_name]

                formated_reflextive_data = self._format_samples(component_reflective_data)
                new_instruction = self.single_proposer(
                    current_instruction=current_instruction, examples_with_feedback=formated_reflextive_data
                ).improved_instruction

                updated_components[component_name] = new_instruction

        return updated_components
    
    def _format_samples(self, samples):
        def render_value(value, level=3):
            # level controls markdown header depth (###, ####, etc.)
            if isinstance(value, dict):
                s = ""
                for k, v in value.items():
                    s += f"{'#' * level} {k}\n"
                    s += render_value(v, min(level + 1, 6))
                if not value:
                    s += "\n"
                return s
            elif isinstance(value, (list, tuple)):
                s = ""
                for i, item in enumerate(value):
                    s += f"{'#' * level} Item {i + 1}\n"
                    s += render_value(item, min(level + 1, 6))
                if not value:
                    s += "\n"
                return s
            else:
                return f"{str(value).strip()}\n\n"
        def convert_sample_to_markdown(sample, examplenum):
            s = f"# Example {examplenum}\n"
            for key, val in sample.items():
                s += f"## {key}\n"
                s += render_value(val, level=3)
            return s
        return "\n\n".join(convert_sample_to_markdown(sample, i + 1) for i, sample in enumerate(samples))


