import asyncio
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from core.database import engine
from core.models import User, UserProfile, ArticleState
from core.config import settings

from services.llm import generate_embedding
from services.email import send_daily_digest

async def generate_daily_digest(user_id: str, user_email: str):
    """Fetches unread articles from Qdrant, cross-references Postgres, and dispatches the email."""
    print(f"\n[DISPATCHER] Assembling digest for {user_email}...")

    async with AsyncSession(engine) as session:
        # Fetch the user's Brain from PostgreSQL
        stmt_profile = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await session.exec(stmt_profile)
        profile = profile_result.one_or_none()

        if not profile or not profile.core_interests:
            print(f"[DISPATCHER] No core interests found for {user_email}. Skipping.")
            return

        # check what have we already sent them?
        stmt_sent = select(ArticleState.qdrant_doc_id).where(
            ArticleState.user_id == user_id,
            ArticleState.emailed == True
        )
        sent_result = await session.exec(stmt_sent)
        already_sent_ids = sent_result.all()

        # Search Qdrant for their topics
        # FastEmbed runs locally on CPU, so we don't need to pass the Groq API key here!
        search_query = " ".join(profile.core_interests + profile.focus_areas)
        query_vector = await generate_embedding(search_query)
        
        client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        
        # Build the Qdrant Filter: Must belong to this user, and MUST NOT be in the sent list
        must_conditions = [
            qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=str(user_id)))
        ]
        
        must_not_conditions = []
        if already_sent_ids:
            must_not_conditions.append(qmodels.HasIdCondition(has_id=list(already_sent_ids)))

        search_results = await client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=qmodels.Filter(
                must=must_conditions,
                must_not=must_not_conditions
            ),
            limit=5, # Top 5 articles a day
            with_payload=True,
            score_threshold=0.40
        )

        if not search_results:
            print(f"[DISPATCHER] No new/unread articles found for {user_email}.")
            return

        # Format articles for the email and update the PostgreSQL db
        articles_to_send = []
        for point in search_results:
            articles_to_send.append({
                "id": point.id,
                "payload": point.payload
            })
            
            # Record that we are sending this article today
            new_state = ArticleState(
                user_id=user_id,
                qdrant_doc_id=str(point.id),
                emailed=True
            )
            session.add(new_state)

        # Dispatch the email!
        # Note: We pass user_id so the email buttons know who clicked them
        send_daily_digest(articles_to_send, user_email, str(user_id))

        # Commit updates to the database
        await session.commit()
        print(f"[DISPATCHER] Digest sent! PostgreSQL ledger updated for {user_email}.")
        
async def run_morning_dispatcher():
    """Wakes up at 8 AM, finds all users, and sends them their personalized emails."""
    print("[MORNING DISPATCHER] Waking up. Preparing daily emails...")
    
    async with AsyncSession(engine) as session:
        # Fetch all active users
        statement = select(User).where(User.encrypted_llm_api_key != None)
        result = await session.exec(statement)
        active_users = result.scalars().all()
        
        if not active_users:
            print("[MORNING DISPATCHER] No active users found. Going back to sleep.")
            return
            
        for user in active_users:
            try:
                # Trigger the email logic we already wrote!
                await generate_daily_digest(user.id, user.email)
            except Exception as e:
                print(f"[DISPATCHER ERROR] Failed to send email to {user.email}: {e}")
                
    print("[MORNING DISPATCHER] All emails sent! See you tomorrow.")