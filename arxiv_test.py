import arxiv  

client = arxiv.Client()


print("Search query sent to arXiv API: 'quantum' with max_results=2 and sorted by submission date.")
search = arxiv.Search(
  query = "quantum",
  max_results = 2,
  sort_by = arxiv.SortCriterion.SubmittedDate,
  # wait for 5 s to avoid hitting rate limits
)

results = client.results(search)
for result in results:
    print(f"Title: {result.title}")
