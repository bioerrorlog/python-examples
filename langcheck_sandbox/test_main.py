from langcheck.metrics.ja.reference_based_text_quality import semantic_similarity

# Dummy outputs
generated_outputs = [
    'メロスは激怒した。',
    'メロスは激しく怒った。',
    'メロスは、激しく、怒った。',
    'セリヌンティウスは待っていた。',
    '単語のベクトル表現は、1960年代における情報検索用のベクトル空間モデルを元に開発された。潜在的意味分析は、特異値分解で次元数を削減することで、1980年代後半に導入された。',
    '1960年以前に、ベクトル表現は開発された。のちに次元数を増幅することにより、潜在分析が導入された。',
    'すみません、ITヘルプデスクに電話で問い合わせてください。',
]

reference_outputs = [
    'メロスは激怒した。',
    'メロスは激怒した。',
    'メロスは激しく怒った',
    'メロスは激怒した。',
    '単語をベクトルとして表現する手法は、1960年代における情報検索用のベクトル空間モデルの開発が元になっている。特異値分解を使用して次元数を削減することにより、1980年代後半に潜在的意味分析が導入された。',
    '単語をベクトルとして表現する手法は、1960年代における情報検索用のベクトル空間モデルの開発が元になっている。特異値分解を使用して次元数を削減することにより、1980年代後半に潜在的意味分析が導入された。',
    '大変申し訳ございませんが、弊社情報部門のヘルプデスクにメールでお問い合わせください。',
]


# Prerequisite: Set OPENAI_API_KEY as an environment variable
def test_semantic_similarity_by_openai():
    results = semantic_similarity(generated_outputs, reference_outputs, model_type='openai')
    print(results)

    assert results > 0.9


def test_semantic_similarity():
    results = semantic_similarity(generated_outputs, reference_outputs)
    print(results)

    assert results > 0.9
