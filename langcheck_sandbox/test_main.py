from langcheck.metrics.ja.reference_based_text_quality import semantic_similarity

# Dummy outputs
generated_outputs = [
    'Black cat the',
    'The black cat is.',
    'The black cat is sitting',
    'The big black cat is sitting on the fence',
    'Usually, the big black cat is sitting on the old wooden fence.',
]

reference_outputs = [
    'Black cat the',
    'The black cat is.',
    'The black cat is sitting',
    'The big black cat is sitting on the fence',
    'Usually, the big black cat is sitting on the old wooden fence.',
]


def test_semantic_similarity():
    results = semantic_similarity(generated_outputs, reference_outputs)
    print(results)

    assert results > 0.9
