import numpy as np
from collections import defaultdict


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def find_top5_matches(test_embedding, db_embeddings):

    all_scores = []

    for student_id, emb_list in db_embeddings.items():
        for emb in emb_list:
            sim = cosine_similarity(test_embedding, emb)
            all_scores.append((sim, student_id))

    all_scores.sort(key=lambda x: x[0], reverse=True)
    return all_scores[:5]


def match_students(test_embeddings, db_embeddings, threshold=0.55):

    predicted_students = []
    similar_students_all = []

    for idx, test_emb in enumerate(test_embeddings):
        top5 = find_top5_matches(test_emb, db_embeddings)

        vote_count = defaultdict(int)
        similar_students = []

        for sim, stid in top5:
            if sim >= threshold:
                vote_count[stid] += 1
                similar_students.append(stid)

        similar_students_all.append(similar_students)

        if vote_count:
            best_match = max(vote_count, key=vote_count.get)
        else:
            best_match = None

        predicted_students.append(best_match)

    return predicted_students, similar_students_all
