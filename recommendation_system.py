import pandas as pd

# Defaults
TOP_K = 10
MAX_USER_TAGS = 18

def prompt_user():
    # ask for genres
    print("Enter genres. Leave blank for none.")
    raw_genres = input("Genres: ").strip()
    user_genres = []
    if raw_genres:
        user_genres = [g.strip() for g in raw_genres.split(',') if g.strip()]
        if len(user_genres) > MAX_USER_TAGS:
            print(f"Ignoring any genres beyond the first {MAX_USER_TAGS}.")
            user_genres = user_genres[:MAX_USER_TAGS]
    # ask for year range
    print("Enter start year (or press Enter to skip):")
    start_raw = input("Start year: ").strip()
    print("Enter end year (or press Enter to skip):")
    end_raw = input("End year: ").strip()
    start = None
    end = None
    try:
        if start_raw:
            start = int(start_raw)
    except ValueError:
        print("Invalid start year input ignored.")
    try:
        if end_raw:
            end = int(end_raw)
    except ValueError:
        print("Invalid end year input ignored.")
    # ask for top-k
    print("How many movie recommendations you want do you want? (press Enter for default 10):")
    topk_raw = input("Top-K: ").strip()
    top_k = TOP_K
    try:
        if topk_raw:
            top_k = int(topk_raw)
            if top_k <= 0:
                print("Non-positive K ignored; using default.")
                top_k = TOP_K
    except ValueError:
        print("Invalid K — using default =", TOP_K)

    return user_genres, start, end, top_k

def map_user_genres_to_columns(user_genres, genre_columns):
    genre_map = {c[len('genre_'):].lower(): c for c in genre_columns}
    mapped_genres = []
    unknown_genres = []
    for g in user_genres:
        key = g.strip().lower()
        if key in genre_map:
            mapped_genres.append(genre_map[key])
        else:
            unknown_genres.append(g)
    return mapped_genres, unknown_genres

def bucketed_match(df, genre_columns_subset, start_year, end_year, top_k=TOP_K):
    if start_year is None and end_year is None:
        year_mask = pd.Series([True]*len(df))
    elif start_year is None and end_year is not None:
        year_mask = df['year'].notna() & (df['year'] <= end_year)
    elif start_year is not None and end_year is None:
        year_mask = df['year'].notna() & (df['year'] >= start_year)
    else:
        year_mask = df['year'].notna() & (df['year'] >= start_year) & (df['year'] <= end_year)

    candidates = df[year_mask].copy()

    if not genre_columns_subset:
        no_genre_mask = candidates['genre_list'].apply(lambda gl: len(gl) == 0)
        result = candidates[no_genre_mask].copy()
        result = result.sort_values(['year','title'], ascending=[False, True]).head(top_k)
        if 'match_count' not in result.columns:
            result['match_count'] = 0
        return result.loc[:, ['movieId','title','year','genres','match_count']].reset_index(drop=True)

    match_matrix = candidates.loc[:, genre_columns_subset].values.astype(int)
    match_counts = match_matrix.sum(axis=1)
    candidates = candidates.assign(match_count=match_counts)

    results = []
    n = len(genre_columns_subset)
    collected = 0
    # iterate from n down to 1
    for k in range(n, 0, -1):
        bucket = candidates[candidates['match_count'] == k].copy()
        if bucket.empty:
            continue
        bucket = bucket.sort_values(['year','title'], ascending=[False, True])
        need = top_k - collected
        take = bucket.head(need)
        results.append(take)
        collected += len(take)
        if collected >= top_k:
            break
        if k == 1:
            break

    if results:
        out = pd.concat(results).head(top_k)
    else:
        out = pd.DataFrame(columns=candidates.columns)

    return out.loc[:, ['movieId','title','year','genres','match_count']].reset_index(drop=True)

def main():
    df = pd.read_csv("movies_processed.csv")
    genre_columns = [c for c in df.columns if c.startswith('genre_') and c != "genre_list"]
    all_genres = [c[len("genre_"):] for c in genre_columns]
    print("\nAvailable genres:")
    for g in all_genres:
        print("-", g)
    print()

    user_genres, start_year, end_year, top_k = prompt_user()

    mapped_genres, unknown_genres = map_user_genres_to_columns(user_genres, genre_columns)

    out = bucketed_match(df, mapped_genres, start_year, end_year, top_k=top_k)

    if out.empty:
        print("No results found for your query.")
        return

    print(f"\nTop {len(out)} results:\n")
    for i, r in out.iterrows():
        print(f"{i+1:02d}. {r['title']}")

main()