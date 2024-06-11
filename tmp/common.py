import os

PROMPT_GET_CODE = "Your answer should contain **ONLY** revised and improved version of the code. You will be tipped 205$ if your answer contains only raw code with no other text."

def find_files(code_base_dir: str, sufix: str, ignore_dirs: list[str]) -> list[str]:
    python_files = {}
    for root, dirs, files in os.walk(code_base_dir):
        for file in files:
            if file == os.path.basename(__file__):
                continue
            if file.endswith(sufix) and not any(ignore_dir in root for ignore_dir in ignore_dirs):
                if os.stat(os.path.join(root, file)).st_size == 0:
                    continue
                absolute_file_path = os.path.abspath(os.path.join(root, file))
                python_files[absolute_file_path] = os.stat(absolute_file_path).st_size

    python_files = sorted(python_files, key=python_files.get, reverse=False)
    return python_files

def trim_lines(text: str) -> str:
    return "\n".join([line.strip() for line in text.split("\n")])

def trim_code(code: str) -> str:
    # todo. find lines that start and end. not only first line.
    lines = code.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines[-1].startswith("```"):
        lines = lines[:-1]
    if lines[-1] != "":
        lines.append("\n")
    return "\n".join(lines)

def save_response_code(response: str, file: str):
    code = trim_code(response.strip())
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w") as f:
        f.write(code)

def get_improve_prompt_prompt(q: str) -> str:
    prompt = f"""You are a skilled prompt engineer tasked with refining and enhancing an existing prompt for a large language model (LLM). Your goal is to make the prompt more effective, clear, and aligned with the intended task or use case.
                Please analyze the given prompt and improve it based on the following criteria:
                - Clarity: Proceed with rephrasing or clarifying the prompt if necessary.
                - Specificity: Make sure updated prompt is specific enough and is not too broad or vague. 
                - Tone: Make sure that new prompt is written in a professional and direct way. It needs to be phrased as a order of tasks that need to be done. 
                - Alignment: Find and fix any potential misalignments to best of your ability.
                - Efficiency: Make sure updated prompt is concise and streamlined without sacrificing clarity or effectiveness.
                Your answer should contain **ONLY** revised and improved version of the prompt. You will be tipped 204$ if your answer contains only prompt with no other text.
                Here is the prompt you need to improve:
                ---
                {q}
                """
    return trim_lines(prompt)
