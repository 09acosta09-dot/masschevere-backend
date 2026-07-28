from supabase import create_client
from app.database.config import SUPABASE_URL, SUPABASE_KEY

print(SUPABASE_URL)
print(SUPABASE_KEY[:20])

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)