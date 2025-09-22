# DARTS: Open Source AI Application Testing Framework

DARTS is a framework designed to test AI models by running YAML-based test cases and generating statistics and visualizations. It supports multiple AI providers, including OpenAI and Ollama, and produces results in CSV and JSONL formats. Additionally, it computes fail/pass statistics for each test case and generates a radar chart (or bar chart) to visualize model performance.
Find out more: <BLOG>

## Requirements

- Python 3.7+
- Required Python packages:
  - `pandas`
  - `numpy`
  - `argparse`
  - `plotly`
  - `yaml`
  - `ollama`
  - `openai`

## Installation

1. Clone the repository:
  ```bash
      git clone https://github.com/marcopedrinazzi/darts.git
      cd darts
  ```
2. Install the required dependencies:
  ```bash
      pip install -r requirements.txt
  ```

## Usage
1. Running Tests
Use the runner.py script to execute YAML-based test cases:
  ```bash
      python darts.py \
        --folder <path-to-yaml-folder> \
        --provider <provider> \
        --model <model-name> \
        --out <output-jsonl-path> \
        --csv <output-csv-path>
  ```

Arguments:
--folder: Path to the folder containing YAML test cases (default: payloads).
--provider: AI provider (ollama or openai).
--model: Target model (e.g., gpt-4o, llama3.1).
--judge-provider: (Optional) Judge provider (defaults to --provider).
--judge-model: (Optional) Judge model (defaults to --model).
--out: Path to the output JSONL file (default: results.jsonl).
--csv: Path to the output CSV file (default: results.csv).

2. Generating Statistics and Charts
Use the table_and_chart.py script to compute statistics and generate radar charts:
  ```bash
      python table_and_chart.py \
        --results-file <input-csv-path> \
        --stats-file <output-stats-csv-path> \
        --chart-file <output-chart-html-path>
  ```

Arguments:
--results-file: Path to the input results CSV file.
--stats-file: Path to save the computed statistics CSV file.
--chart-file: Path to save the radar chart HTML file.

Payloads
The test cases for the framework are defined in YAML files. Each YAML file specifies a unique test case, including the prompts to be tested, the judging criteria, and metadata.

## Example Payload
```yaml
id: <test-id>
name: <test-name>
topics:
  - <topic>
judge: |
  <judge instructions>

  Your output must be in the following JSON format:

  {
    "test_id": "<test-id>",
    "test_name": "<test-name>",
    "verdict": "Pass" | "Fail",
    "reason": "Clear, concise explanation for the verdict. Reference specific parts of the LLM output that justify the decision."
  }

  Only return the JSON. Do not include any additional text or commentary.
prompts:
  - <prompt1>
  - <prompt1>
```

Explanation:
- id: Unique identifier for the test case.
- name: Descriptive name of the test case.
- topics: Topics covered by the test case.
- judge: Instructions for the judge (AI evaluator) to assess the output. **The only requirement I set is to always produce an output in JSON following the schema outlined above in order to keep consistency.**
- prompts: List of prompts to be tested against the AI model.

### OWASP-AITG-APP
Do you want to test your model with the OWASP-AITG-APP prompts? Check out Joey Melo's work https://github.com/joey-melo/payloads/tree/main/OWASP%20AITG-APP 

## Output
### Test Results
- JSONL: Contains detailed results for each test case.
- CSV: Summarized results with fields like test_id, test_name, verdict, and reason.

### Statistics
- CSV: Contains fail/pass statistics for each test case, including percentages.

### Chart
- HTML: Interactive radar (or bar) chart visualizing fail percentages for each model. The script creates a radar chart if the number of rows in the dataset is greater than 5, if not it creates a bar chart.

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.
