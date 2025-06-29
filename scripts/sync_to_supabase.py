import os
import re
import frontmatter
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # Optional for local testing

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BUCKET_NAME = "blog-posts"
TABLE_NAME = "blog_metrics"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
POSTS_DIR = Path(__file__).parent.parent / "01_blogs" / "posts"

def slugify(filename: str) -> str:
    name = Path(filename).stem
    return re.sub(r'\W+', '-', name.lower()).strip('-')

def upload_markdown_files():
    for md_path in POSTS_DIR.rglob("*.md"):
        rel_path = md_path.relative_to(POSTS_DIR)
        storage_path = str(rel_path)

        # Upload to storage
        with open(md_path, "rb") as f:
            content = f.read()

        print(f"Uploading {storage_path} to storage bucket...")

        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": "text/markdown"},
            upsert=True
        )

        if hasattr(response, "error") and response.error:
            print(f"Failed to upload {storage_path}: {response.error.message}")
            continue
        else:
            print(f"Uploaded {storage_path}")

        # Generate slug for the blog metrics table
        slug = slugify(storage_path)

        # Check if entry already exists in blog_metrics
        existing = supabase.table(TABLE_NAME).select("slug").eq("slug", slug).execute()
        if existing.data and len(existing.data) > 0:
            print(f"Entry already exists in blog_metrics for '{slug}', skipping insert.")
        else:
            print(f"Inserting blog_metrics entry for '{slug}'")
            supabase.table(TABLE_NAME).insert({
                "slug": slug,
                "views": 0,
                "likes": 0
            }).execute()

if __name__ == "__main__":
    upload_markdown_files()
