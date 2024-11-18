from fastapi import FastAPI, UploadFile, Form, BackgroundTasks, HTTPException, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import redis
from datetime import datetime
import groq
from typing import Optional, List
import asyncio
from utils.email_utils import send_email, get_esp_client
from utils.google_sheets_utils import connect_google_sheets
from utils.scheduler_utils import EmailScheduler
from models.email_data import EmailData, EmailStatus
import uvicorn
from dotenv import load_dotenv
import os
import logging
from auth.google_auth import GoogleAuthManager
from fastapi.responses import JSONResponse
import io
from fastapi import Request
from utils.storage_utils import StorageManager
from models.csv_data import CSVUploadResponse
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Dashboard")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Initialize Redis with error handling
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test Redis connection
    redis_client.ping()
    logger.info("Successfully connected to Redis")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    raise

# Initialize Groq client for LLM
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY", "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"))

# Initialize ESP client (SendGrid in this case)
esp_client = get_esp_client()

# Initialize scheduler
email_scheduler = EmailScheduler()

auth_manager = GoogleAuthManager()

class EmailRequest(BaseModel):
    prompt_template: str
    schedule_time: Optional[str]
    batch_size: Optional[int] = 50
    interval_minutes: Optional[int] = 60

@app.on_event("startup")
async def startup_event():
    """Runs on application startup"""
    try:
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection verified during startup")
        
        # Clear any stale data (optional)
        # redis_client.flushdb()
    except Exception as e:
        logger.error(f"Startup check failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Runs on application shutdown"""
    try:
        redis_client.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

@app.post("/generate_email/")
async def generate_email(prompt_template: str, company: str, location: str, products: str):
    try:
        prompt = f"""
        Generate a professional email based on the following template and information:
        Template: {prompt_template}
        Company: {company}
        Location: {location}
        Products: {products}
        Make it personalized and professional.
        """
        
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=1000
        )
        
        return {"generated_content": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule_emails/")
async def schedule_emails(request: EmailRequest, background_tasks: BackgroundTasks):
    try:
        keys = redis_client.keys("email:*")
        total_emails = len(keys)
        
        if request.schedule_time:
            schedule_time = datetime.strptime(request.schedule_time, "%Y-%m-%d %H:%M")
        else:
            schedule_time = datetime.now()
            
        batch_size = request.batch_size
        interval_minutes = request.interval_minutes
        
        for i in range(0, total_emails, batch_size):
            batch_keys = keys[i:i + batch_size]
            batch_time = schedule_time + pd.Timedelta(minutes=interval_minutes * (i // batch_size))
            
            for key in batch_keys:
                email_data = EmailData.parse_obj(redis_client.hgetall(key))
                email_data.scheduled_time = batch_time.isoformat()
                email_data.status = 'Scheduled'
                redis_client.hset(key, mapping=email_data.dict())
                
                background_tasks.add_task(
                    email_scheduler.schedule_email,
                    email_data,
                    request.prompt_template,
                    batch_time
                )
        
        return {
            "message": "Emails scheduled successfully",
            "total_scheduled": total_emails,
            "batches": (total_emails + batch_size - 1) // batch_size
        }
    except Exception as e:
        logger.error(f"Error scheduling emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_analytics():
    try:
        keys = redis_client.keys("email:*")
        analytics = {
            "total_emails": len(keys),
            "status_breakdown": {},
            "delivery_status": {},
            "scheduled_breakdown": {
                "past": 0,
                "upcoming": 0
            }
        }
        
        now = datetime.now()
        
        for key in keys:
            email_data = EmailData.parse_obj(redis_client.hgetall(key))
            
            analytics["status_breakdown"][email_data.status] = \
                analytics["status_breakdown"].get(email_data.status, 0) + 1
            
            analytics["delivery_status"][email_data.delivery_status] = \
                analytics["delivery_status"].get(email_data.delivery_status, 0) + 1
            
            if email_data.scheduled_time:
                scheduled_time = datetime.fromisoformat(email_data.scheduled_time)
                if scheduled_time < now:
                    analytics["scheduled_breakdown"]["past"] += 1
                else:
                    analytics["scheduled_breakdown"]["upcoming"] += 1
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/esp-webhook/")
async def esp_webhook(event_data: dict):
    """Handle ESP webhook events for email tracking"""
    try:
        email = event_data.get("email")
        event_type = event_data.get("event")
        
        keys = redis_client.keys("email:*")
        for key in keys:
            email_data = EmailData.parse_obj(redis_client.hgetall(key))
            if email_data.email == email:
                email_data.delivery_status = event_type.capitalize()
                redis_client.hset(key, mapping=email_data.dict())
                break
        
        return {"message": "Webhook processed successfully"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()
        return {
            "status": "healthy",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )

@app.get("/api/auth/google")
async def google_auth():
    """Start Google OAuth flow"""
    try:
        auth_url, state = await auth_manager.get_authorization_url()
        return JSONResponse({
            "auth_url": auth_url,
            "state": state
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/callback")
async def auth_callback(auth_data: dict):
    try:
        code = auth_data.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code is required")

        # Exchange the code for tokens and retrieve user info
        user_info = await get_user_info_from_google(code)  # Implement this function
        email = user_info.get("email")

        return {"email": email}
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/google_sheets")
async def google_sheets_auth():
    try:
        # Initialize Google Auth Manager
        auth_manager = GoogleAuthManager()
        
        # Get authorization URL
        auth_url = auth_manager.get_authorization_url(
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        return {
            "success": True,
            "auth_url": auth_url
        }
    except Exception as e:
        logger.error(f"Error initiating Google Sheets auth: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.get("/api/get_csv_fields")
async def get_csv_fields():
    try:
        storage_manager = StorageManager()
        fields = await storage_manager.get_csv_fields()
        return {"fields": fields}
    except Exception as e:
        logger.error(f"Error getting CSV fields: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule_emails")
async def schedule_emails(
    background_tasks: BackgroundTasks,
    email_data: EmailData
):
    try:
        keys = redis_client.keys("email:*")
        total_emails = len(keys)
        
        logger.info(f"Total emails to schedule: {total_emails}")
        
        if total_emails == 0:
            raise HTTPException(status_code=400, detail="No emails to schedule.")

        if email_data.schedule_time:
            schedule_time = datetime.strptime(email_data.schedule_time, "%Y-%m-%d %H:%M")
        else:
            schedule_time = datetime.now()
        
        batch_size = email_data.batch_size
        interval_minutes = email_data.interval_minutes
        
        for i in range(0, total_emails, batch_size):
            batch_keys = keys[i:i + batch_size]
            logger.info(f"Processing batch: {batch_keys}")
            
            if not batch_keys:
                logger.warning("No keys found for the current batch.")
                continue
            
            batch_time = schedule_time + pd.Timedelta(minutes=interval_minutes * (i // batch_size))
            
            for key in batch_keys:
                email_data = EmailData.parse_obj(redis_client.hgetall(key))
                email_data.scheduled_time = batch_time.isoformat()
                email_data.status = 'Scheduled'
                redis_client.hset(key, mapping=email_data.dict())
                
                background_tasks.add_task(
                    email_scheduler.schedule_email,
                    email_data,
                    email_data.prompt_template,
                    batch_time
                )
        
        return {
            "message": "Emails scheduled successfully",
            "total_scheduled": total_emails,
            "batches": (total_emails + batch_size - 1) // batch_size
        }
    except Exception as e:
        logger.error(f"Error scheduling emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_email")
async def generate_email(request: dict):
    try:
        # Initialize Groq client
        groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Replace placeholders with sample data
        template = request["prompt_template"]
        for key, value in request.items():
            if key != "prompt_template":
                template = template.replace(f"{{{key}}}", value)
        
        # Generate content using Groq
        response = await groq_client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": "You are an email content generator. Generate professional email content based on the template."
            }, {
                "role": "user",
                "content": template
            }],
            model="mixtral-8x7b-32768",
            temperature=0.7,
        )
        
        generated_content = response.choices[0].message.content
        return {"generated_content": generated_content}
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/email-events")
async def handle_email_events(request: Request):
    try:
        payload = await request.json()
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        
        for event in payload:
            tracking_id = event.get('tracking_id')
            if tracking_id:
                key = f"email:{tracking_id}"
                current_status = event.get('event')
                
                if current_status in ['delivered', 'opened', 'bounced', 'dropped']:
                    redis_client.hset(key, 'delivery_status', current_status)
                    
                # Broadcast update through WebSocket
                await broadcast_analytics_update()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def broadcast_analytics_update():
    try:
        analytics = await get_analytics()
        for connection in active_connections:
            await connection.send_json(analytics)
    except Exception as e:
        logger.error(f"Error broadcasting update: {str(e)}")

active_connections: List[WebSocket] = []

@app.websocket("/ws/analytics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
            analytics = await get_analytics()
            await websocket.send_json(analytics)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        active_connections.remove(websocket)
from io import StringIO

@app.post("/api/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
        # Store CSV data in Redis
        redis_client.set('current_csv_data', contents.decode('utf-8'))  # Store as string
        
        return CSVUploadResponse(
            message=f"Successfully saved {len(df)} records",
            fields=list(df.columns),
            total_records=len(df)
        )
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Error uploading CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/store_email")
async def store_email(email_data: dict):
    try:
        email = email_data.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Store email in Redis
        redis_client.hset(f"email:{email}", mapping={"status": "connected", "delivery_status": "pending"})
        
        return {"message": "Email stored successfully"}
    except Exception as e:
        logger.error(f"Error storing email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_user_emails")
async def get_user_emails():
    try:
        # Retrieve all keys matching the email pattern
        keys = redis_client.keys("email:*")
        emails = []

        for key in keys:
            # Extract the email from the key
            email = key.split(":")[1]  # Assuming keys are in the format "email:<email>"
            emails.append(email)

        return {"emails": emails}
    except Exception as e:
        logger.error(f"Error retrieving user emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_csv_preview")
async def get_csv_preview():
    try:
        csv_data = redis_client.get('current_csv_data')
        if not csv_data:
            raise HTTPException(status_code=404, detail="No CSV data found.")
        
        df = pd.read_csv(StringIO(csv_data))  # Convert string back to DataFrame
        preview = df.head().to_dict(orient='records')  # Get the first few rows as a preview
        return {"preview": preview}
    except Exception as e:
        logger.error(f"Error getting CSV preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")