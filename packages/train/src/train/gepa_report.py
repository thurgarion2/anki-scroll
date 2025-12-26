import matplotlib.pyplot as plt
from jinja2 import Template
import markdown
from dspy.teleprompt.gepa.gepa import DspyGEPAResult


def generate_gepa_report(result: DspyGEPAResult, chart_path: str = "gepa_chart.png") -> str:
    """
    Generate an HTML report for a DspyGEPAResult.

    Args:
        result: The DspyGEPAResult to report on.
        chart_path: Path to save the chart PNG file.

    Returns:
        HTML string of the report.
    """
    # Generate chart
    iterations = list(range(len(result.val_aggregate_scores)))
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, result.val_aggregate_scores, marker='o')
    plt.title('GEPA Optimization: Iterations vs Validation Aggregate Scores')
    plt.xlabel('Iteration')
    plt.ylabel('Validation Aggregate Score')
    plt.grid(True)
    plt.savefig(chart_path)
    plt.close()

    # Prepare iteration data
    iteration_data = [
        {
            'index': i,
            'score': result.val_aggregate_scores[i]
        }
        for i in range(len(result.candidates))
    ]

    # Extract and render prompts
    candidate_prompts = []
    for i, candidate in enumerate(result.candidates):
        prompts = {}
        for name, pred in candidate.named_predictors():
            instructions = pred.signature.instructions
            html_instructions = markdown.markdown(instructions)
            prompts[name] = html_instructions
        candidate_prompts.append({
            'index': i,
            'prompts': prompts
        })

    # HTML template
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GEPA Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .chart { text-align: center; margin-bottom: 20px; }
            .iteration { margin-bottom: 10px; }
            .expandable { cursor: pointer; background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }
            .expandable:hover { background-color: #e0e0e0; }
            .content { display: none; padding: 10px; border: 1px solid #ccc; margin-top: 5px; }
        </style>
        <script>
            function toggle(id) {
                var content = document.getElementById(id);
                if (content.style.display === "none" || content.style.display === "") {
                    content.style.display = "block";
                } else {
                    content.style.display = "none";
                }
            }
        </script>
    </head>
    <body>
        <h1>GEPA Optimization Report</h1>
        <div class="chart">
            <img src="{{ chart_path }}" alt="GEPA Chart">
        </div>
        <h2>Iterations</h2>
        <ul>
            {% for item in iteration_data %}
            <li class="iteration">Iteration {{ item.index }}: Score {{ item.score }}</li>
            {% endfor %}
        </ul>
        <h2>Prompt Summaries</h2>
        {% for candidate in candidate_prompts %}
        <div class="expandable" onclick="toggle('candidate-{{ candidate.index }}')">Candidate {{ candidate.index }}</div>
        <div id="candidate-{{ candidate.index }}" class="content">
            {% for name, prompt_html in candidate.prompts.items() %}
            <h3>{{ name }}</h3>
            <div>{{ prompt_html | safe }}</div>
            {% endfor %}
        </div>
        {% endfor %}
    </body>
    </html>
    """

    template = Template(html_template)
    html = template.render(chart_path=chart_path, iteration_data=iteration_data, candidate_prompts=candidate_prompts)
    return html