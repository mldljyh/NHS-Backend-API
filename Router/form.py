from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import requests
from Database.database import get_db, rollback_to_savepoint
from fastapi import APIRouter, Depends, BackgroundTasks
from starlette.status import *
import os
from dotenv import load_dotenv
from fastapi import Request, Form
import uuid
from Service.user_service import UserService

router = APIRouter(prefix="/form", tags=["form"])

load_dotenv(".env")
BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL")
BOT_ID = os.getenv("BOT_ID")
REST_API_KEY = os.getenv("REST_API_KEY")

templates = Jinja2Templates(directory="Templates")
@router.post("/create")
async def create_form(request: Request):
    try:
        data = await request.json()
        uid = data['userRequest']['user']['id']
        if UserService.get_user(uid) is None:
            UserService.save_user(UserService.to_user_entity(uid))
        form_id = str(uuid.uuid4())
        form_id = UserService.create_form(uid, form_id)
        url = BACKEND_SERVER_URL+"/form/submit/"+form_id
        json_form = {
            "version": "2.0",
            "template": {
                "outputs": [
                {
                    "basicCard": {
                    "title": "사용자 정보 입력",
                    "description": "안녕하세요, 국민건강비서의 가상 복지상담관 김건강입니다. 아래 시작하기 버튼을 눌러 상담에 필요한 기본적인 정보를 알려주시면 꼼꼼히 확인해보겠습니다!",
                    "thumbnail": {
                        "imageUrl": "https://i.ibb.co/hWzLvCr/Geongang-Kim.jpg"
                    },
                    "buttons": [
                        {
                        "action":  "webLink",
                        "label": "시작하기",
                        "webLinkUrl": url
                        }
                    ]
                    }
                }
                ]
            }
            }
        return JSONResponse(status_code=200, content=json_form)
    except Exception as e:
        raise e
        return JSONResponse(status_code=500, content={"message": str(e)})
    
@router.get("/submit/{form_id}")
async def get_form(request: Request, form_id: str):
    try:
        if UserService.get_form(form_id):
            return templates.TemplateResponse("form.html", {"request": request, "form_id": form_id})
        return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"message": "만료된 폼입니다."})
    except Exception as e:
        raise e
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"message": str(e)})

@router.post("/submit/{form_id}")
async def submit_form(request: Request, form_id: str, age: int = Form(...), gender: str = Form(...), disease: str = Form(None), subscription: str = Form(None)):
    try:
        if uid := UserService.get_user_by_form_id(form_id):
            UserService.remove_form(form_id)
            UserService.save_user_info(uid, age, gender, disease, subscription)
            json_form = {
                "event": {
                    "name": "onSubscribe"
                },
                "user": [
                    {"type": "botUserKey", "id": uid}
                ]
            }
            header = {
                "Authorization": "KakaoAK "+ REST_API_KEY,
                "Content-Type": "application/json"
            }
            requests.post("https://bot-api.kakao.com/v2/bots/"+BOT_ID+"/talk", json=json_form, headers=header)
            return JSONResponse(status_code=200, content=json_form)
        return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"message": "만료된 폼입니다."})
    except Exception as e:
        raise e
        return JSONResponse(status_code=500, content={"message": str(e)})