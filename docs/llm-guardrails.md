# LLM application basics

## Embeddings and retrieval
An embedding turns text into a vector so that similar meanings are close together. Retrieval-augmented generation (RAG) splits documents into chunks, embeds them, stores them in a vector database and retrieves the nearest chunks for each question before calling the model.

## Hallucinations and guardrails
Models can state false facts with confidence. Reduce this by answering only from the retrieved context, citing sources, and replying "I don't know" when retrieval finds nothing relevant. Validate structured outputs against a schema before using them.

## Cost and latency
Cost grows with the number of input and output tokens. Keep prompts short, retrieve only the top few chunks, cache repeated requests and stream long answers so users see output early.

## Evaluation
Build a small dataset of questions with known source documents and measure retrieval quality, for example hit rate at k and mean reciprocal rank. Run it in CI so a change to chunking or prompts cannot silently make answers worse.
