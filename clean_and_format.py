import pandas as pd
import re

def extract_year(title):
    if not isinstance(title, str): return None
    m = re.search(r'\((\d{4})\)\s*$', title)
    return int(m.group(1)) if m else None

def split_genres(g):
    if pd.isna(g): return []
    return [x.strip() for x in g.split('|') if x.strip() and x.strip()!='(no genres listed)']

df = pd.read_csv("movies.csv")

# removing duplicates
df = df.drop_duplicates(subset=["title"])

# extract year from the title
df['year'] = df['title'].apply(extract_year)

# formates genres properly
df['genre_list'] = df['genres'].apply(split_genres)

# creating a multi-hot matrix for faster vector operation
all_genres = sorted({g for gl in df['genre_list'] for g in gl})
for g in all_genres:
    df[f'genre_{g}'] = df['genre_list'].apply(lambda gl: int(g in gl))

df.to_csv("movies_processed.csv", index=False)