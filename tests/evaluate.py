import argparse
import json
import time

from src import config, rag

QUESTIONS_FILE = config.BASE_DIR / "tests" / "test_questions.json"
SAVED_DIR = config.BASE_DIR / "tests" / "saved_answers"

# Pause between Gemini calls so the free tier rate limit is not hit.
PAUSE_SECONDS = 6

# Retrieval is tested for each of these top-k values in a single run.
K_VALUES = (2, 4)


def load_questions():
    with open(QUESTIONS_FILE, encoding="utf-8") as file:
        return json.load(file)


def normalize(text):
    """Lowercase, and treat hyphens, underscores and extra spaces as one space."""
    text = text.lower().replace("-", " ").replace("_", " ")
    return " ".join(text.split())


def run_retrieval():
    """Free test, no Gemini calls. Two measures for each top-k value.

    File hit: the expected file appears in the top-k chunks.
    Keyword hit: every expected keyword appears in the text of the top-k chunks.
    """
    questions = [q for q in load_questions() if q["answerable"]]
    file_hits = {k: 0 for k in K_VALUES}
    word_hits = {k: 0 for k in K_VALUES}
    max_k = max(K_VALUES)

    for q in questions:
        chunks = rag.retrieve(q["question"], k=max_k)
        marks = []
        for k in K_VALUES:
            top = chunks[:k]
            files = [c.metadata.get("file_name") for c in top]
            text = normalize(" ".join(c.page_content for c in top))
            file_ok = q["expected_source"] in files
            word_ok = all(normalize(w) in text for w in q["expected_keywords"])
            file_hits[k] += int(file_ok)
            word_hits[k] += int(word_ok)
            marks.append(
                f"k={k} file:{'hit ' if file_ok else 'MISS'} words:{'hit ' if word_ok else 'MISS'}"
            )
        print(f"Q{q['id']:>2} " + " | ".join(marks))

    print()
    total = len(questions)
    for k in K_VALUES:
        print(f"Top-{k} file hit rate:    {file_hits[k]}/{total} = {100 * file_hits[k] / total:.0f}%")
        print(f"Top-{k} keyword hit rate: {word_hits[k]}/{total} = {100 * word_hits[k] / total:.0f}%")


def score(questions, saved):
    """Check saved answers against the expected keywords."""
    correct = 0
    scored = 0
    total_seconds = 0.0

    for q in questions:
        item = saved.get(str(q["id"]))
        if item is None:
            print(f"Q{q['id']:>2} no saved answer yet")
            continue
        scored += 1
        total_seconds += item["seconds"]
        answer = normalize(item["answer"])
        if q["answerable"]:
            passed = all(normalize(word) in answer for word in q["expected_keywords"])
        else:
            passed = normalize(rag.NOT_FOUND_TEXT) in answer
        correct += int(passed)
        print(f"Q{q['id']:>2} {'PASS' if passed else 'FAIL'} | {q['question'][:60]}")

    if scored:
        print(f"\nAccuracy: {correct}/{scored} = {100 * correct / scored:.0f}%")
        print(f"Average response time: {total_seconds / scored:.1f} seconds")


def run_answers(label):
    """Ask Gemini each question. Answers are saved so no call is repeated."""
    SAVED_DIR.mkdir(exist_ok=True)
    path = SAVED_DIR / f"{label}.json"
    saved = {}
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))

    questions = load_questions()
    for q in questions:
        key = str(q["id"])
        if key in saved:
            continue
        start = time.time()
        try:
            result = rag.ask(q["question"])
        except Exception as error:
            print(f"Q{q['id']:>2} failed ({type(error).__name__}). Run again to retry it.")
            continue
        saved[key] = {
            "answer": result["answer"],
            "sources": result["sources"],
            "seconds": round(time.time() - start, 2),
        }
        path.write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Q{q['id']:>2} saved ({saved[key]['seconds']} seconds)")
        time.sleep(PAUSE_SECONDS)

    print()
    score(questions, saved)


def main():
    parser = argparse.ArgumentParser(description="Evaluate the RAG assistant.")
    parser.add_argument("mode", choices=["retrieval", "answers"])
    parser.add_argument("--label", default="baseline", help="name for the saved answers file")
    args = parser.parse_args()

    if args.mode == "retrieval":
        run_retrieval()
    else:
        run_answers(args.label)


if __name__ == "__main__":
    main()