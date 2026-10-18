# Use Cases — Cite v1.0

Actor for all use cases: **User** (student, researcher, or demo visitor). External systems: Claude (LLM), Web Search API.
Common precondition for UC-02 to UC-06: the user has opened the Cite web app, and the daily cost cap and rate limit are not reached.

---

## UC-01 Upload a PDF
**Traces to:** BR-01
**Preconditions:** None.

**Main flow**
1. User selects one PDF file and clicks Upload.
2. System checks the file type and size.
3. System extracts text page by page, splits it into overlapping chunks that keep their page number, and creates embeddings for each chunk.
4. System stores the chunks and marks the document as "Ready" in the document list.

**Alternate / exception flows**
- 2a. File is not a PDF, or is over 20 MB / 50 pages: system rejects it with a clear message. Nothing is stored.
- 3a. Some pages have no text (scanned): system stores the rest and warns which pages were skipped.
- 3b. No page has text: system marks the document "Failed — no text found".

**Postconditions:** The document's chunks are searchable by `search_documents`.

---

## UC-02 Ask a question answered from documents
**Traces to:** BR-01, BR-06
**Preconditions:** At least one document is Ready and contains the answer.

**Main flow**
1. User types a question (e.g. "What sample size did the Smith paper use?") and submits it.
2. System sends the question and the tool definitions to Claude.
3. Claude asks to call `search_documents`; system runs it and returns the matching chunks.
4. Claude decides it has enough information and writes the final answer.
5. System shows the answer with citations like `[smith2024.pdf, p. 4]` and an "Agent steps" panel listing each tool call.

**Alternate / exception flows**
- 3a. First search finds nothing useful: Claude searches again with different words (up to the step limit).
- 3b. A tool fails (e.g. database error): the error is returned to Claude, which may retry or continue; the user sees the error in Agent steps.

**Postconditions:** Answer and every step are saved in the database.

---

## UC-03 Ask a question that needs the web
**Traces to:** BR-02, BR-04, BR-06
**Preconditions:** None (documents not needed).

**Main flow**
1. User asks a question about recent or general information (e.g. "What is the latest stable Python version?").
2. Claude calls `web_search`; system returns titles, URLs, and snippets.
3. Claude writes the answer citing results as `[title](URL)`.
4. System shows the answer; web citations open in a new tab.

**Alternate / exception flows**
- 2a. Search API is down or times out: the error is returned to Claude, which tells the user it could not reach the web.
- 2b. A result contains instructions (e.g. "ignore previous instructions"): Claude treats it as data and does not follow it.

**Postconditions:** Answer and steps saved.

---

## UC-04 Ask a question that needs a calculation
**Traces to:** BR-03, BR-06
**Preconditions:** None.

**Main flow**
1. User asks a question with math (e.g. "If revenue grew from 4.2M to 5.1M, what is the growth in %?").
2. Claude calls `calculator` with an expression such as `(5.1 - 4.2) / 4.2 * 100`.
3. System evaluates it safely and returns `21.43`.
4. Claude answers using the result; Agent steps shows the expression and result.

**Alternate / exception flows**
- 2a. Expression is invalid or unsafe (e.g. contains code, or divides by zero): calculator returns an error; Claude fixes the expression or explains the problem.

**Postconditions:** Answer and steps saved.

---

## UC-05 Ask a question that combines sources
**Traces to:** BR-01, BR-02, BR-03, BR-04, BR-06
**Preconditions:** A Ready document holds part of the answer.

**Main flow**
1. User asks a multi-part question (e.g. "My report says we had 1,200 users in 2025. How does that compare to the industry average growth rate?").
2. Claude calls `search_documents` to find the figure in the report.
3. Claude calls `web_search` to find the industry figure.
4. Claude calls `calculator` to compare them.
5. Claude writes one answer citing both the document page and the web source.

**Alternate / exception flows**
- 2–4a. Step limit (6) is reached before the answer is complete: system stops the loop and Claude gives a partial answer that says what is missing.
- 3a. Web gives no usable figure: Claude answers the document part and says the rest could not be found.

**Postconditions:** Answer and steps saved.

---

## UC-06 Ask a question with no answer available
**Traces to:** BR-05, BR-06
**Preconditions:** None.

**Main flow**
1. User asks a question that the documents and the web cannot answer (e.g. "What did page 12 of my report say?" when the report has 5 pages, or a private fact).
2. Claude searches the documents and/or the web and finds nothing relevant.
3. Claude replies that it could not find an answer, says where it looked, and gives no citations or made-up facts.

**Alternate / exception flows**
- 2a. Search returns loosely related results: Claude does not stretch them into an answer; it says the sources do not answer the question.

**Postconditions:** The "no answer" response and steps are saved.
